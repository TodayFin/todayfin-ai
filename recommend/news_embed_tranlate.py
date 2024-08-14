# -*- coding: utf-8 -*-

# 모델 다운로드
# pip install gdown
# gdown "https://drive.google.com/uc?id=1Av37IVBQAAntSe1X3MOAl5gvowQzd2_j"
# 파일 크기 1.65G

from dotenv import load_dotenv
import os
from pymongo import MongoClient
from bson.objectid import ObjectId

import pandas as pd
import numpy as np

import gensim
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from googletrans import Translator

# 한 번만 실행해도 됩니다.
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')


# DB 연결 - Cluster : NewsAPi-cluster, Database : newsDB, Collection : news
load_dotenv()
mongodb = os.getenv('MONGODB')
client = MongoClient(mongodb)

# 데이터베이스 및 컬렉션 선택
db = client['newsDB']
news_collection = db['news']

embed_translate = pd.DataFrame(list(news_collection.find({'title_trans': ''})))

print(f'임베딩 생성이 필요한 데이터: {len(embed_translate)}')
print('#################### 데이터 조회 완료 ####################')

# title 전처리
preprocessed_title = []
stop_words = set(stopwords.words('english'))

for i in embed_translate['title']:
    tokenized_title = word_tokenize(i) # 토크나이저 변경 가능
    result = []
    for word in tokenized_title: # 모든 단어 소문자화, 생략 가능
        word = word.lower()

        if word not in stop_words: # 불용어 제거
            if len(word) > 2: # 단어 길이가 2이하인 단어 삭제
                result.append(word)
    preprocessed_title.append(result)
print('#################### 데이터 전처리 완료 ####################')

# 구글의 사전 학습 Word2Vec 모델 사용
# 모델 로드하면 RAM 사용량 5.7GB까지 상승, 모델 로드 약 1~2분
word2vec_model = gensim.models.KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin.gz', binary=True)
print('#################### 모델 로드 완료 ####################')

# 임베딩 함수
def get_document_vectors(document_list):
    document_embedding_list = []
    vec_0_count = 0

    # 각 문서에 대해서
    for line in document_list:
        doc2vec = None
        count = 0

        for word in line:
            if word in word2vec_model.key_to_index:
                count += 1
                # 해당 문서에 있는 모든 단어들의 벡터값을 더한다.
                if doc2vec is None:
                    doc2vec = word2vec_model[word]
                else:
                    doc2vec = doc2vec + word2vec_model[word]

        if doc2vec is not None and count > 0:  # 단어 벡터가 존재하고, count가 0보다 큰 경우
            # 단어 벡터를 모두 더한 벡터의 값을 문서 길이로 나눠준다.
            doc2vec = doc2vec / count
            document_embedding_list.append(doc2vec)
        else:
            # 빈 문서나 단어가 없는 문서의 경우, 0 벡터를 추가 (차원 일치를 위해)
            vec_0_count += 1
            zero_vector = np.zeros(word2vec_model.vector_size)
            document_embedding_list.append(zero_vector)
    print(f'빈 문서나 단어가 없는 문서의 개수: {vec_0_count}')
    # 각 문서에 대한 문서 벡터 리스트를 리턴
    return document_embedding_list

document_embedding_list = get_document_vectors(preprocessed_title)
embed_translate['embedding'] = document_embedding_list
print('문서 벡터의 수 :',len(document_embedding_list))
print('#################### 데이터 임베딩 완료 ####################')

for idx in embed_translate._id:
    val = embed_translate[embed_translate['_id'] == idx]['embedding'].to_list()[0].tolist()
    news_collection.update_one({'_id': idx}, {'$set': {'embedding': val}})
print('#################### 임베딩 DB 저장 완료 ####################')


# googletrans 번역기 설정
translator = Translator()

def translate_article(article):
    try:
        title_trans = translator.translate(article['title'], src='en', dest='ko').text
        article_trans = translator.translate(article['article'], src='en', dest='ko').text

        news_collection.update_one(
            {'_id': article['_id']},
            {'$set': {'title_trans': title_trans, 'article_trans': article_trans}}
        )
        # print(f"Article with ID {article['_id']} translated and updated successfully.")
    except Exception as e:
        print(f"Error translating article with ID {article['_id']}: {e}")

def translate_main():
    # 공백인 데이터 가져오기
    articles = news_collection.find({'title_trans': '', 'article_trans': ''})

    for article in articles:
        translate_article(article)

translate_main()
print('#################### 번역 DB 저장 완료 ####################')