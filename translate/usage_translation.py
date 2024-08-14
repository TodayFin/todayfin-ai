# -*- coding: utf-8 -*-
"""Usage_Translation.py

데이터를 입력받아 구글트랜스 api로 번역 수행 후 결과를 json 형태로 반환합니다.
"""


# 예시 데이터
# 이 형식으로 데이터를 입력하세요
"""
example_data = {
    '_id': '66ad8755a059303c88b51b50',
    'title': 'Airline cuts popular snack due to increased turbulence - Fox Business',
    'category': 'business',
    'article': 'Korean Air will stop serving the popular snack instant ramen on some flights because of increased turbulence.\n\nThe airline will cut the cups of instant noodles from the food options available to economy passengers on its long-haul flights as "part of proactive safety measures in response to increased turbulence, aimed at preventing burn accidents," a Korean Air spokesperson told FOX Business.\n\nGET FOX BUSINESS ON THE GO BY CLICKING HERE\n\nKorean Air will provide other snacks to passengers in its revamped in-flight snack service.\n\nThe change, earlier reported by Reuters and Time, will take effect in mid-August.\n\n"To enhance passenger satisfaction and diversity snack options, a self-service snack bar is available on long-haul flights," the Korean Air spokesperson also told FOX Business.\n\nIn July, the airline said it was "undertaking a comprehensive review of service strategies to ensure the highest standards of safety and travel experience for its passengers" due to a higher frequency of turbulence.\n\nTHESE ARE THE FLIGHT ROUTES WITH THE MOST TURBULENCE\n\nOne new procedure that Korean Air has already implemented is new timing for the end of cabin services on medium- and long-haul flights. That has changed from 20 minutes prior to touchdown to 40 minutes.\n\n"Turbulence has become a persistent and growing problem in recent years with the number of incidents doubling in Q1 2024 compared to Q1 2019," the airline said in July. "Turbulence is becoming more frequent, especially as the aircraft descends, due to large temperature changes between altitudes."\n\nThe severity of turbulence encountered by an aircraft can range from light to extreme, according to Weather.gov.\n\nCLICK HERE TO READ MORE ON FOX BUSINESS',
    'urlToImage': 'https://a57.foxnews.com/static.foxbusiness.com/foxbusiness.com/content/uploads/2024/08/0/0/Korean-Air-Airbus-A380-landing.jpg?ve=1&tl=1',
    'publishedAt': '2024-08-01T15:57:00Z',
    'source': 'Fox Business',
    'author': 'Aislinn Murphy',
    'title_trans': '',
    'trans': '',
    'embedding': []
}

"""

import json
from googletrans import Translator
from time import sleep

translator = Translator()

def translate_google(text):
    try:
        sleep(2)  # Rate limit 피하기 위해 지연시간 추가
        result = translator.translate(text, dest='ko')
        return result.text
    except Exception as e:
        print(f"Error: {e}")
        return None

# "example_data['article']" 부분을 실제 데이터로 변경하세요
text_to_translate = example_data['article']
translated_text_google = translate_google(text_to_translate)
print(f"Translated Text by Googletrans: {translated_text_google}")

# JSON 형식으로 변환
# 원문과 번역문으로 이루어진 json파일을 반환합니다 필요에따라 형식을 수정할 수 있습니다
translation_data = {
    "original_article": text_to_translate,
    "translated_article": translated_text_google
}
translation_json = json.dumps(translation_data, ensure_ascii=False, indent=4)

# JSON 파일로 저장
with open('translation_result.json', 'w', encoding='utf-8') as f:
    f.write(translation_json)



print(translation_json)
