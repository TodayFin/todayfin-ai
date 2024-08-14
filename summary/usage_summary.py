# -*- coding: utf-8 -*-
"""
Usage_summary.py

이 스크립트는 사전 학습된 T5 모델을 로드하고, 주어진 텍스트를 요약한 후
결과를 JSON 형식으로 출력합니다.
"""

# 작동 확인용 예시 데이터 
#이 형식으로 데이터를 입력 받아야합니다
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
import torch
import gc

# model.py 에서 모델을 로드합니다
from model import load_model

model, tokenizer, device = load_model()


# 요약할 내용을 설정합니다.
# "example_data['article']" 를 실제 데이터로 수정하세요
text = example_data['article'] 

# 텍스트를 요약하는 기능
def summarize_text(text, model, tokenizer, device):
    input_text = "summarize: " + text
    input_ids = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True).to(device)

    with torch.no_grad():
        summary_ids = model.generate(input_ids, max_length=150, min_length=40, length_penalty=2.0, num_beams=4, early_stopping=True)

    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    # Free memory
    del input_ids, summary_ids
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return summary

# 텍스트를 요약
summary = summarize_text(text, model, tokenizer, device)
print(summary)

# Free model and tokenizer memory
del model, tokenizer
gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()

# 요약 결과를 JSON 형식으로 변환
summary_json = json.dumps({"summary": summary}, ensure_ascii=False, indent=4)

# JSON 형식으로 저장되었는지 확인
print(summary_json)

# JSON 파일로 저장
with open('summary.json', 'w', encoding='utf-8') as f:
    f.write(summary_json)
