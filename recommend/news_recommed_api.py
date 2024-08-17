# API 통신 코드

# uvicorn main:app --reload 로 로컬 실행
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from bson.objectid import ObjectId

from dotenv import load_dotenv
import os

import numpy as np
import pandas as pd

app = FastAPI()

# request body 데이터 설정
class UserLog(BaseModel):
    news_id: List[str] # 유저의 뉴스 로그

# DB load
load_dotenv()
mongodb = os.getenv('MONGODB')

# client = MongoClient(SIMON_MONGO)
client = MongoClient(mongodb)
db = client['newsDB']
news_collection = db['news']

# API
@app.post("/recommend/")
async def top5_recommendation(user_log: UserLog):
    '''
    추가 예정
    - 최신 기사 고려
    - 카테고리 고려
    '''
    news_id = [ObjectId(x) for x in user_log.news_id]
    read = pd.DataFrame(news_collection.find({'_id': {'$in': news_id}}))
    read['embedding'] = read['embedding'].apply(np.array) # 벡터 연산 가능하게 넘파이로 저장
    
    user_vec = read['embedding'].sum()

    pipeline = [
        {
            '$vectorSearch': {
                'index': 'recommend_vector_index', 
                'exact': False, # ANN, True시 ENN
                'path': 'embedding', 
                'queryVector': user_vec.tolist(), 
                'numCandidates': 150,
                '_id': {'$nin': news_id}, # 이미 조회한 기사 제외 
                'limit': 5
                }
        }, {
            '$project': {
                '_id': 1, 
                # 'title': 1, 
                # 'title_trans':1,
                # 'category': 1, 
                'score': {
                    '$meta': 'vectorSearchScore'
                    }
                }
            }
        ]
    result = [str(x['_id']) for x in news_collection.aggregate(pipeline)]
    score = [x['score'] for x in news_collection.aggregate(pipeline)]
    print(score) # log에 성능 출력용
    return {'recommed': result}


