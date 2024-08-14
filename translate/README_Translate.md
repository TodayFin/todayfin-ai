# todayfin-ai

# 통합 SNS 기반 뉴스 및 금융 정보 서비스

## 프로젝트 소개
이 미션에서는 사용자가 뉴스 요약 및 분석, 금융 정보를 제공받을 수 있는 SNS 서비스를 개발합니다. 사용자에게 최신 뉴스를 요약하여 제공하고, 금융 정보를 시각화 및 분석하여 제공하는 기능을 포함합니다. 서비스는 뉴스 및 금융 데이터 API와 통합되어야 하며, 사용자 맞춤형 추천 기능도 포함합니다. 또한, 사용자가 뉴스와 금융 정보를 공유하고 토론할 수 있는 SNS 기능을 갖추어야 합니다.

## 요구 사항
프로젝트를 실행하기 위해 필요한 요구 사항입니다:
- Python 3.8 이상
- pip
- pymongo[srv] --upgrade DB이용시
- googletrans==4.0.0-rc1

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

5. 번역 API 설정:
    ```python
    from googletrans import Translator

# googletrans 번역기 설정
translator = Translator()

def translate_article(article):
    try:
        title_trans = translator.translate(article['title'], src='en', dest='ko').text
        article_trans = translator.translate(article['article'], src='en', dest='ko').text

        collection.update_one(
            {'_id': article['_id']},
            {'$set': {'title_trans': title_trans, 'trans': article_trans}}
        )
        print(f"Article with ID {article['_id']} translated and updated successfully.")
    except Exception as e:
        print(f"Error translating article with ID {article['_id']}: {e}")

def main():
    # 공백인 데이터 가져오기
    articles = collection.find({'trans': '', 'title_trans': ''})

    for article in articles:
        translate_article(article)

if __name__ == "__main__":
    main()

    ```

## 사용 방법
이 프로젝트의 주요 기능은 입력된 텍스트를 번역하여 제공하는 것입니다.

예시에서는 몽고DB에 연결하여 예시데이터를 가져와 번역한 후, 결과를 DB에 저장합니다.
다음은 텍스트 번역을 위한 예시 코드입니다:

```python
from googletrans import Translator

# googletrans 번역기 설정
translator = Translator()

def translate_article(article):
    try:
        title_trans = translator.translate(article['title'], src='en', dest='ko').text
        article_trans = translator.translate(article['article'], src='en', dest='ko').text

        collection.update_one(
            {'_id': article['_id']},
            {'$set': {'title_trans': title_trans, 'trans': article_trans}}
        )
        print(f"Article with ID {article['_id']} translated and updated successfully.")
    except Exception as e:
        print(f"Error translating article with ID {article['_id']}: {e}")

def main():
    # 공백인 데이터 가져오기
    articles = collection.find({'trans': '', 'title_trans': ''})

    for article in articles:
        translate_article(article)

if __name__ == "__main__":
    main()
