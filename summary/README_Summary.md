# todayfin-ai

# 통합 SNS 기반 뉴스 및 금융 정보 서비스

## 프로젝트 소개
이 미션에서는 사용자가 뉴스 요약 및 분석, 금융 정보를 제공받을 수 있는 SNS 서비스를 개발합니다. 사용자에게 최신 뉴스를 요약하여 제공하고, 금융 정보를 시각화 및 분석하여 제공하는 기능을 포함합니다. 서비스는 뉴스 및 금융 데이터 API와 통합되어야 하며, 사용자 맞춤형 추천 기능도 포함합니다. 또한, 사용자가 뉴스와 금융 정보를 공유하고 토론할 수 있는 SNS 기능을 갖추어야 합니다.

## 사용된 요약 모델
shivaniNK8 유저의 모델을 일부 수정하여 사용하였습니다.

https://github.com/shivaniNK8/News-Article-Text-Summarizer-Transformer

파인튜닝된 모델은 허깅페이스 개인 저장소에서 확인할 수 있습니다.

https://huggingface.co/kdk07718/t5-small-finetuned-cnn-news

## 사용된 데이터 셋
Dataset Link: https://paperswithcode.com/dataset/cnn-daily-mail-1

## 요구 사항
프로젝트를 실행하기 위해 필요한 요구 사항입니다:
- Python 3.8 이상
- pip
- torch 2.3.1+cu121
- transformers 4.42.4

## 설치 방법

1. 저장소 클론:
    ```sh
    git clone https://github.com/KTB-LuckyVicky/todayfin-ai.git
    cd todayfin-ai
    ```

2. 가상 환경 생성 및 활성화 (옵션):
    ```sh
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3. 의존성 설치:
    ```sh
    pip install -r requirements.txt
    ```

4. 환경 변수 설정:
    프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 필요한 환경 변수를 설정합니다.
    ```env
    DATABASE_URL=your_database_url
    ```

5. 허깅페이스 키 설정:
    허깅페이스 모델을 사용하기 위해서는 허깅페이스 API 키가 필요할 수 있습니다. 
    다음 코드를 실행하여 키를 설정하세요.
    ```python
    from huggingface_hub import notebook_login
    notebook_login()
    ```
    허깅페이스 오류 발생 시 위 코드를 사용하여 허깅페이스 키를 입력하면 해결됩니다.

6. 모델 및 토크나이저 다운로드:
    초기 실행 시 허깅페이스에서 모델과 토크나이저를 다운로드합니다.
    이 기능은 model.py 를 실행하면 자동으로 이루어집니다.
    ```python
    from transformers import T5Tokenizer, T5ForConditionalGeneration
    import torch

    # Model and tokenizer loading
    model_name = "kdk07718/t5-small-finetuned-cnn-news"
    tokenizer = T5Tokenizer.from_pretrained(model_name)

    # Load the model and move to GPU if available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = T5ForConditionalGeneration.from_pretrained(model_name).to(device)

    # Optimize memory usage by using mixed precision (fp16)
    if torch.cuda.is_available():
        model.half()
    ```

## 사용 방법
이 프로젝트의 주요 기능은 입력된 텍스트를 요약하여 제공하는 것입니다.
Usage_summary.py 파일을 실행하여 입력 형식에 맞게 데이터를 입력하면 요약을 출력합니다.


다음은 텍스트 요약을 위한 예시 코드입니다:

```python
import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration

def summarize_text(text, model, tokenizer, device):
    input_text = "summarize: " + text
    input_ids = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True).to(device)

    with torch.no_grad():
        summary_ids = model.generate(
            input_ids,
            max_length=150,      # 생성할 요약의 최대 길이
            min_length=40,       # 생성할 요약의 최소 길이
            length_penalty=2.0,  # 길이 패널티
            num_beams=4,         # 빔 서치에서 사용할 빔의 수
            early_stopping=True  # 모든 빔이 끝나는 토큰을 생성하면 중지
        )

    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

if __name__ == "__main__":
    # Model and tokenizer loading
    model_name = "kdk07718/t5-small-finetuned-cnn-news"
    tokenizer = T5Tokenizer.from_pretrained(model_name)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = T5ForConditionalGeneration.from_pretrained(model_name).to(device)
    if torch.cuda.is_available():
        model.half()
    
    # Example usage
    text = "The stock market is showing signs of recovery as..."
    summary = summarize_text(text, model, tokenizer, device)
    print("Summary:", summary)
