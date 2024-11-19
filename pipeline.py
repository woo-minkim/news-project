# pipeliine.py 역할 
# 1. 데이터 수집: GDELT API를 사용하여 지정된 기업과 관련된 뉴스 기사를 수집.
# 2. 데이터 추출: newspaper 라이브러리를 사용하여 기사 본문과 제목을 추출.
# 3. 데이터 분석: OpenAI GPT 모델을 사용하여 감성 분석을 수행.
# 4. 데이터 저장: 분석된 데이터를 MongoDB에 저장.
# -> 이후 Streamlit을 사용하여 저장된 데이터를 시각화할 수 있음.
from prompt_template import prompt_template

from openai import OpenAI
from gdeltdoc import GdeltDoc, Filters
from newspaper import Article
from pymongo import MongoClient

import datetime

from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)
model = "gpt-4o-mini"
gd = GdeltDoc() #GdeltDoc 클래스의 인스턴스 생성, Gdelt 데이터베이스에 접근 가능
mongo_client = MongoClient(host="localhost", port=27017) #MongoDB 서버와 연결 
db = mongo_client["NewsProject"] #"NewsProject" 데이터베이스에 접근
collection = db["NewsAnalysisDate"] #"NewsAnalysisDate" 컬렉션에 접근, 이곳에 분석된 뉴스 기사의 데이터를 저장


# query를 기반으로 chatGPT 답변 생성 함수
def chatgpt_generate(query):
  messages = [{ #GPT모델에게 전달할 메시지 리스트
    "role": "system", #모델의 역할과 성격 설정
    "content": "You are a helpful assistant."
  }, 
  { #사용자로부터 받은 질문
    "role": "user",
    "content": query
  }]
  response = openai_client.chat.completions.create(model=model, messages = messages)
  answer = response.choices[0].message.content
  return answer

# GDELT API를 이용하여 뉴스 기사 URL 가져오기
def get_url(keyword):
  f = Filters(
    start_date = "2024-05-01",
    end_date = "2024-05-25",
    num_records = 10,
    keyword = "Microsoft",
    domain = "nytimes.com",
    country = "US",
  )  
  articles = gd.article_search(f) # (Pandas) DataFrame 형태로 반환
  return articles

# 뉴스 기사 URL을 이용하여 뉴스 기사 내용 가져오기
def get_article(df):
  urls = df["url"] # 기사 URL을 저장할 리스트
  titles = df["title"] # 기사 제목을 저장할 리스트
  texts = [] # 기사 본문을 저장할 리스트
  for url in urls:
    article = Article(url) # newspaper3k 라이브러리의 Article 클래스로 기사 객체 생성
    article.download() #지정된 URL에서 기사의 HTML 데이터 다운로드
    article.parse() #다운로드한 HTML을 파싱하여 기사의 본문을 추출
    texts.append(article.text) #추출한 기사 본문을 리스트에 추가
  return texts, titles

# 지정된 기업 리스트(orgs)에 대해 GDELT API를 사용해 관련 뉴스를 수집하고 GPT 모델을 통해 분석한 후 결과를 MOngoDB에 저장
def analysis():
  orgs = ["microsoft", "apple"]  # 분석할 기업 이름을 저장한 리스트
  
  for org in orgs:  
    df = get_url(org)  # `get_url` 함수를 호출하여 해당 기업과 관련된 메타데이터를 가져옴
    dates = df["seendate"]  # 데이터프레임에서 기사 날짜 정보를 가져옴
    texts, titles = get_article(df)  # `get_article` 함수로 기사 본문과 제목을 가져옴
    
    for idx, text in enumerate(texts):  # 가져온 기사 본문에 대해 반복
      news_item = {}  # 개별 뉴스 아이템을 저장할 딕셔너리
      answer = chatgpt_generate(prompt_template + text)  # GPT 모델로 기사 분석
      try:
          answer_list = eval(answer)  # GPT 응답을 리스트 형태로 변환 
          news_item["text"] = text  # 기사 본문 저장
          news_item["title"] = titles[idx]  # 기사 제목 저장
          [item.update({"seendate": dates[idx]}) for item in answer_list]  # 응답 리스트에 기사 날짜 추가
          news_item["sentiment"] = answer_list  # 감성 분석 결과 저장
          news_item["date"] = datetime.datetime.now()  # 현재 날짜와 시간을 저장
          insert_id = collection.insert_one(news_item).inserted_id  # MongoDB에 데이터 삽입 후 ID 반환
          print(insert_id)  # 삽입된 데이터의 ID 출력
      except:
          continue  # 에러 발생 시 해당 루프를 건너뜀

  return  # 함수 종료

analysis()

# Sentiment Scoring? 
# 텍스트 데이터에서 긍정적, 부정적, 중립적 감정을 분석하고,
# 각 감정에 대한 점수를 부여하는 과정 