# API 통신 코드
# uvicorn news_recommend_api:app --reload 로 로컬 실행
from fastapi import FastAPI
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

# request body 데이터 설정
class UserId(BaseModel):
    id: int # 유저의 id

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

## 전처리 파이프라인
# 데이터 로드
raw_news = pd.DataFrame(news_collection.find())
def preprocessing(temp):
    # 임베딩 분할 300columns
    temp_emb = temp['embedding'].apply(pd.Series)
    temp_emb.columns = ['embed_'+str(i) for i in temp_emb.columns]

    # 필요한 변수만 선택, 임베딩과 결합
    temp_select = pd.concat([temp[['_id','category', 'publishedAt', 'source']], temp_emb], axis = 1)
    # 뉴스 수가 적은 기사 etc로 변경
    source_major = ['Benzinga', 'Zacks Commentary', 'Business Standard', 'Motley Fool', 'GlobeNewswire']
    source = [x if x in source_major else 'etc' for x in temp_select['source']]
    temp_select['source'] = source

    # 날짜 처리 및 정규화(현재 시각과의 차이, timestamp 기준)
    current_time = datetime.now().timestamp()
    temp_select['publishedAt'] = pd.to_datetime(temp_select['publishedAt'])
    temp_select['timediff'] = temp_select['publishedAt'].apply(lambda x: current_time - x.timestamp())
    scaler = StandardScaler()
    temp_select['timediff'] = scaler.fit_transform(temp_select['timediff'].to_numpy().reshape(-1,1))
    temp_select.drop('publishedAt', axis = 1, inplace=True) 

    return temp_select

news_total = preprocessing(temp = raw_news)

# catergory 정수 인코딩
cat_dic = {}
order_cat = sorted(news_total['category'].unique())
order_source = sorted(news_total['source'].unique())
for count, i in enumerate(order_cat):
    cat_dic[i] = count

# source 정수 인코딩
source_dic = {}
for count, i in enumerate(order_source):
    source_dic[i] = count

# news onehot encoding
news_total['category'] = pd.Categorical(news_total['category'], categories=order_cat, ordered=True)
news_total['source'] = pd.Categorical(news_total['source'], categories=order_source, ordered=True)
news_total = pd.get_dummies(news_total, columns=['category', 'source'])

# news 시간순 정렬
news_sorted = news_total.sort_values(by = ['timediff'])

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
    user_data = search_data(user_id = user_id.id)

    user_log = user_data.get('log')
    if user_log is None:
        user_log = []
    else:
        user_log = ast.literal_eval(user_log)

    user_cat = ast.literal_eval(user_data['category'])
    
    # 로그 없는 신규 유저
    if len(user_log) == 0 :
        result = []
        for cat in user_cat:
            result += news_sorted[news_sorted[f'category_{cat}'] == True]['_id'][:2].to_list()
        result = list(map(str,result))
        return {'recommend': result[:5]}
    
    news_id = [ObjectId(x) for x in user_log]
    
    read = pd.DataFrame(news_collection.find({'_id': {'$in': news_id}}))
    read['embedding'] = read['embedding'].apply(np.array) # 벡터 연산 가능하게 넘파이로 저장
    user_source = read['source'].mode().values[0]
    
    # user embedding
    user_vec = read['embedding'].sum()/len(user_log)
    # category onehot encoding dim=6
    user_cat_onehot = [0]*len(order_cat)
    for i in user_cat:
        user_cat_onehot[cat_dic[i]] = 1
    user_vec = np.append(user_vec, user_cat_onehot)
    # timediff dim=1
    user_timediff = 0
    user_vec = np.append(user_vec, user_timediff)
    # source onehot encoding dim = 6
    user_source_onehot = [0]*len(order_source)
    user_source_onehot[source_dic[user_source]] = 1
    # final user_vec dim = 313
    user_vec = np.append(user_vec, user_source_onehot)
    
    notread = news_total[~news_total['_id'].isin(user_log)]

    notread['cos_sim'] = cosine_similarity(user_vec.reshape(1,-1), notread.iloc[:,1:].to_numpy())[0]
    notread = notread.sort_values(by='cos_sim', ascending=False)
    
    result = list(map(str,notread['_id'][:5].to_list()))
    score = notread['cos_sim'][:5].to_list()
    print(f'user_id: {user_id.id} \n추천 기사와의 유사도: {score}') # log에 성능 출력용
    return {'recommend': result}
