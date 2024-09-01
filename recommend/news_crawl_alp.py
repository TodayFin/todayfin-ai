# -*- coding: utf-8 -*-
# 20240813 16:40 첫 DB 저장

import pandas as pd

import requests
from newspaper import Article
from datetime import datetime, timedelta

from pymongo import MongoClient
from bson.objectid import ObjectId

from dotenv import load_dotenv
import os

# api key load
load_dotenv()
apikey = os.getenv('AlPHAVANTAGEAPI')
mongodb = os.getenv('MONGODB')


# cats_full = ['blockchain', 'earnings', 'ipo', 'mergers_and_acquisitions',
#         'finacial_markets', 'economy_fiscal', 'economy_monetary', 'economy_macro',
#         'energy_transportation', 'finace', 'life_sciences', 'manufacturing',
#         'real_estate', 'retail_wholesale', 'technology']

# 토픽이 너무 디테일해서 일단 간단한 토픽만 수집
# 20240902 finace 삭제, finance 수집
cats_sub = ['finance', 'life_sciences', 'manufacturing',
        'real_estate', 'retail_wholesale', 'technology']

# 1일 간격으로 수집
today = datetime.now().strftime('%Y%m%dT%H%M')
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%dT%H%M')
today4log = datetime.today().strftime('%Y%m%d') # 로그용 날짜 변수

temp = {}
for cat in cats_sub:
    url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&&apikey={apikey}&time_from={yesterday}&time_to={today}&topics={cat}'
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data['feed'])
    df['category'] = cat
    temp[cat] = df

news_df = pd.concat(temp)
news_df.reset_index(drop=True, inplace=True)
news_df = news_df.rename(columns = {'time_published': 'publishedAt', 'authors': 'author', 'banner_image': 'urlToImage'})
# author 자료형 변경 list -> str
news_df['author'] = news_df['author'].apply(lambda x: ','.join(x))
print(f'#################### {today4log} Alpha Vantage API 데이터 조회 완료 ####################')

# 원문 추출
# 300개 기준 3분정도
article_list = []
for i, url in enumerate(news_df['url']):
    try:
        article = Article(url = url, follow_meta_refresh = True, verbose = True )
        article.download()
        article.parse()
        article_list.append(article.text)
    except :
        article_list.append('')
        pass
news_art = pd.concat([news_df, pd.Series(article_list, name = 'article')], axis = 1)
news_fin = news_art[news_art['article'] != ''].reset_index(drop=True)
print(f'#################### {today4log} 원문 추출 완료 ####################')

# DB 연결 - Cluster : NewsAPi-cluster, Database : newsDB, Collection : news
client = MongoClient(mongodb)

# 데이터베이스 선택
db = client['newsDB']

# 컬렉션 선택(백업 컬렉션에 저장)
news_collection_backup = db['news_backup']

query = []
for i in range(len(news_fin)):
    temp_dic = {}
    temp_dic['title'] = news_fin["title"][i]
    temp_dic['title_trans'] = ''
    temp_dic['category'] = news_fin["category"][i]
    temp_dic['article'] = news_fin["article"][i]
    temp_dic['article_trans'] = ''
    temp_dic['url'] = news_fin["url"][i]
    temp_dic['urlToImage'] = news_fin["urlToImage"][i]
    temp_dic['publishedAt'] = news_fin["publishedAt"][i]
    temp_dic['source'] = news_fin["source"][i]
    temp_dic['author'] = news_fin["author"][i]
    temp_dic['embedding'] = ''
    query.append(temp_dic)

# 삽입
result = news_collection_backup.insert_many(query)
print(f'#################### {today4log} news 정보 DB 저장 완료 ####################')