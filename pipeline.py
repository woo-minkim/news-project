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
gd = GdeltDoc()
mongo_client = MongoClient(host="localhost", port=27017)
db = mongo_client["NewsProject"]
collection = db["NewsAnalysisDate"]


# chatGPT 답변 생성 함수
def chatgpt_generate(query):
  messages = [{
    "role": "system", 
    "content": "You are a helpful assistant."
  }, 
  {
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
  articles = gd.article_search(f)
  return articles

# 뉴스 기사 URL을 이용하여 뉴스 기사 내용 가져오기
def get_article(df):
  urls = df["url"]
  titles = df["title"]
  texts = []
  for url in urls:
    article = Article(url)
    article.download()
    article.parse()
    texts.append(article.text)
  return texts, titles

def analysis():
  orgs = ["microsoft", "apple"]  # 분석할 기업 이름을 저장한 리스트
  
  for org in orgs:  
    df = get_url(org)  # `get_url` 함수를 호출하여 해당 기업과 관련된 데이터를 가져옴
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