# -*- coding: utf-8 -*-

import pandas as pd

import requests
from newspaper import Article

from pymongo import MongoClient
from bson.objectid import ObjectId

from dotenv import load_dotenv
import os

# api key load
load_dotenv()
newsapi = os.getenv('NEWSAPI')
mongodb = os.getenv('MONGODB')

# news api로 기사 정보 수집
cats = ['business','entertainment','general','health','science','sports','technology']
temp = {}
for cat in cats:
    url = f'https://newsapi.org/v2/top-headlines?pageSize=100&country=us&apiKey={newsapi}&category={cat}'
    response = requests.get(url)
    data = response.json()
    headline_df = pd.DataFrame(data['articles'])
    headline_df['category'] = cat
    temp[cat] = headline_df

headline_full = pd.concat(temp)
print('#################### newAPI 데이터 조회 완료 ####################')

# source 변수의 딕셔너리에서 name만 추출하여 다시 source에 저장
headline_full['source'] = headline_full['source'].copy().apply(lambda x: x['name'])

# 인터넷 기사 원문 링크 리스트
idx = headline_full['description'].isna()
headline_clean = headline_full[~idx].reset_index(drop=True)
headline_clean['article'] = ''

# 원문 출력
for i, url in enumerate(headline_clean['url']):
    try:
        article = Article(url = url, follow_meta_refresh = True, verbose = True )
        article.download()
        article.parse()
        headline_clean['article'][i] = article.text
    except :
        pass

temp1 = headline_clean[['title', 'category', 'article', 'url', 'urlToImage', 'publishedAt', 'source', 'author']]
temp2 = temp1[temp1['article'] != ''].reset_index(drop=True)
print('#################### 원문 추출 완료 ####################')

# DB 연결 - Cluster : NewsAPi-cluster, Database : newsDB, Collection : news

client = MongoClient(mongodb)

# 데이터베이스, 컬렉션 선택
db = client['newsDB']
news_collection = db['news']

query = []
for i in range(len(temp2)):
    temp_dic = {}
    temp_dic['title'] = temp2["title"][i]
    temp_dic['title_trans'] = ''
    temp_dic['category'] = temp2["category"][i]
    temp_dic['article'] = temp2["article"][i]
    temp_dic['article_trans'] = ''
    temp_dic['url'] = temp2["url"][i]
    temp_dic['urlToImage'] = temp2["urlToImage"][i]
    temp_dic['publishedAt'] = temp2["publishedAt"][i]
    temp_dic['source'] = temp2["source"][i]
    temp_dic['author'] = temp2["author"][i]
    temp_dic['embedding'] = ''
    query.append(temp_dic)

# 데이터 삽입
result = news_collection.insert_many(query)
print('#################### news 정보 DB 저장 완료 ####################')