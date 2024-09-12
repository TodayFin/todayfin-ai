# API 통신 코드
# uvicorn news_recommend_api:app --reload 로 로컬 실행
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

from pymongo import MongoClient
from bson.objectid import ObjectId
import pymysql
from sshtunnel import SSHTunnelForwarder

from dotenv import load_dotenv
import os
import json
from datetime import datetime
import ast
import schedule
import time
import threading

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

# DB load
load_dotenv()
mongodb = os.getenv('MONGODB')
client = MongoClient(mongodb)
db = client['newsDB']
news_collection = db['news']

tunnel = SSHTunnelForwarder((os.getenv('SSHHOST'), 22),
                            ssh_username='ec2-user',
                            ssh_pkey=os.getenv('PEMKEY'), # pem key 경로
                            remote_bind_address=(os.getenv('MARIAHOST'), 3306),
                            local_bind_address=('127.0.0.1', 3308))

tunnel.start()

mariadb_config = {
    'host': tunnel.local_bind_address[0], 
    'port': tunnel.local_bind_address[1],
    'user': os.getenv('MARIAUSER'),
    'password': os.getenv('MARIAPASSWORD'),
    'database': 'TodayFin',
    'cursorclass': pymysql.cursors.DictCursor  # 결과를 dictionary 형태로 반환
}

news_total = None
news_sorted = None
cat_dic = {}
source_dic = {}

def preprocessing(temp):
    # 임베딩 분할 300columns
    temp_emb = temp['embedding'].apply(pd.Series)
    temp_emb.columns = ['embed_'+str(i) for i in temp_emb.columns]

    # 필요한 변수만 선택, 임베딩과 결합
    temp_select = pd.concat([temp[['_id','category', 'publishedAt', 'source']], temp_emb], axis=1)
    
    # 뉴스 소스 처리
    source_major = ['Benzinga', 'Zacks Commentary', 'Business Standard', 'Motley Fool', 'GlobeNewswire']
    temp_select['source'] = temp_select['source'].apply(lambda x: x if x in source_major else 'etc')

    # 날짜 처리 및 정규화
    current_time = datetime.now().timestamp()
    temp_select['publishedAt'] = pd.to_datetime(temp_select['publishedAt'])
    temp_select['timediff'] = temp_select['publishedAt'].apply(lambda x: current_time - x.timestamp())
    scaler = StandardScaler()
    temp_select['timediff'] = scaler.fit_transform(temp_select['timediff'].to_numpy().reshape(-1,1))
    temp_select.drop('publishedAt', axis=1, inplace=True) 

    return temp_select

def update_full_dataset():
    global news_total, news_sorted, cat_dic, source_dic

    print("Starting full dataset update...")
    start_time = time.time()

    # MongoDB에서 모든 뉴스 데이터 로드
    raw_news = pd.DataFrame(news_collection.find())
    
    # 전처리 수행
    news_total = preprocessing(raw_news)

    # 카테고리와 소스에 대한 원-핫 인코딩
    order_cat = sorted(news_total['category'].unique())
    order_source = sorted(news_total['source'].unique())
    
    for count, i in enumerate(order_cat):
        cat_dic[i] = count
    for count, i in enumerate(order_source):
        source_dic[i] = count

    news_total['category'] = pd.Categorical(news_total['category'], categories=order_cat, ordered=True)
    news_total['source'] = pd.Categorical(news_total['source'], categories=order_source, ordered=True)
    news_total = pd.get_dummies(news_total, columns=['category', 'source'])

    # 시간순 정렬
    news_sorted = news_total.sort_values(by=['timediff'])

    end_time = time.time()
    print(f"Full dataset update completed. Time taken: {end_time - start_time:.2f} seconds")
    print(f"Total news articles processed: {len(news_total)}")

schedule.every().day.at("17:30").do(update_full_dataset)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 스케줄 체크

# FastAPI 실행 시 초기 데이터 로드 및 스케줄러 실행
@app.on_event("startup")
async def startup_event():
    update_full_dataset()  # 초기 데이터 로드
    threading.Thread(target=run_scheduler, daemon=True).start()

# 수동으로 데이터셋 업데이트를 트리거하는 엔드포인트
@app.post("/update_dataset/")
async def trigger_dataset_update(background_tasks: BackgroundTasks):
    background_tasks.add_task(update_full_dataset)
    return {"message": "Full dataset update triggered successfully"}

# mariadb
# 유저 정보 조회 함수 유저 id -> log, category
def search_data(user_id):
    conn = pymysql.connect(**mariadb_config, charset = 'utf8')
    cur = conn.cursor()
    try:
        sql = '''
        SELECT log, category FROM User WHERE _id = %s
        '''
        cur.execute(sql, (user_id, ))
        result = cur.fetchone()
    finally:
        conn.close()
    return result

# request body 데이터 설정
class UserId(BaseModel):
    id: int # 유저의 id

# API
@app.post("/recommend/")
async def top5_recommendation(user_id: UserId):
    '''
    추가 예정
    - 최신 기사 고려 -> timediff
    - 선호 카테고리 고려 -> category onehot
    - 유저가 가장 많이 읽은 신문사 고려 -> source onehot
    - 유저 로그가 없을 때 -> 선호 카테고리 별 가장 최신 기사 추천
    - 유저 로그의 중복 데이터 처리 -> backend
    '''
    global news_total, news_sorted, cat_dic, source_dic

    user_data = search_data(user_id=user_id.id)

    user_log = user_data.get('log')
    if user_log is None:
        user_log = []
    else:
        user_log = ast.literal_eval(user_log)

    user_cat = ast.literal_eval(user_data['category'])
    
    # 로그 없는 신규 유저
    if len(user_log) == 0:
        result = []
        for cat in user_cat:
            result += news_sorted[news_sorted[f'category_{cat}'] == True]['_id'][:2].to_list()
        # result = list(map(str, result))
        documents = pd.DataFrame(news_collection.find({"_id": {"$in": result[:5]}}))
        result_df = documents[['_id', 'title_trans', 'publishedAt', 'urlToImage']].copy()
        # ObjectId를 문자열로 변환
        result_df['_id'] = result_df['_id'].astype(str)
        
        # 날짜 형식 변환 (ISO 형식 문자열로 변환)
        # result_df['publishedAt'] = result_df['publishedAt'].dt.isoformat()
        
        # 컬럼 이름 변경
        result_df = result_df.rename(columns={
            '_id': 'id',
            'title_tran': 'title',
            'publishedAt': 'date',
            'urlToImage': 'image'
        })
        
        # DataFrame을 딕셔너리 리스트로 변환
        result_list = result_df.to_dict('records')
        return {'recommend': result_list}
    
    news_id = [ObjectId(x) for x in user_log]
    
    read = pd.DataFrame(news_collection.find({'_id': {'$in': news_id}}))
    read['embedding'] = read['embedding'].apply(np.array)
    user_source = read['source'].mode().values[0]
    news_total['_id_str'] = news_total['_id'].astype(str)
    
    # user embedding
    user_vec = read['embedding'].sum() / len(user_log)
    # category onehot encoding
    user_cat_onehot = [0] * len(cat_dic)
    for i in user_cat:
        user_cat_onehot[cat_dic[i]] = 1
    user_vec = np.append(user_vec, user_cat_onehot)
    # timediff
    user_timediff = 0
    user_vec = np.append(user_vec, user_timediff)
    # source onehot encoding
    user_source_onehot = [0] * len(source_dic)
    # 사용자의 source 처리
    source_major = ['Benzinga', 'Zacks Commentary', 'Business Standard', 'Motley Fool', 'GlobeNewswire']
    if user_source not in source_major:
        user_source = 'etc'
    user_source_onehot[source_dic[user_source]] = 1
    user_vec = np.append(user_vec, user_source_onehot)
    
    notread = news_total[~news_total['_id_str'].isin(user_log)]
    notread = notread.drop('_id_str', axis=1)
    notread['cos_sim'] = cosine_similarity(user_vec.reshape(1,-1), notread.iloc[:,1:].to_numpy())[0]
    notread = notread.sort_values(by='cos_sim', ascending=False)
    
    # result = list(map(str, notread['_id'][:5].to_list()))
    documents = pd.DataFrame(news_collection.find({"_id": {"$in": notread['_id'][:5].to_list()}}))
    result_df = documents[['_id', 'title_trans', 'publishedAt', 'urlToImage']].copy()
    # ObjectId를 문자열로 변환
    result_df['_id'] = result_df['_id'].astype(str)
    
    # 날짜 형식 변환 (ISO 형식 문자열로 변환)
    # result_df['publishedAt'] = result_df['publishedAt'].dt.isoformat()
    
    # 컬럼 이름 변경
    result_df = result_df.rename(columns={
        '_id': 'id',
        'title_trans':'title',
        'publishedAt': 'date',
        'urlToImage': 'image'
    })
    
    # DataFrame을 딕셔너리 리스트로 변환
    result_list = result_df.to_dict('records')

    score = notread['cos_sim'][:5].to_list()
    print(f'user_id: {user_id.id} \n추천 기사와의 유사도: {score}')  # log에 성능 출력용
    return {'recommend': result_list}
