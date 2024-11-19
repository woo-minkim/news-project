# Streamlit Application의 역할 
# pipeline.py에서 저장된 데이터를 조회 및 시각화하는 역할을 함

import streamlit as st  # Streamlit 라이브러리 import (웹 애플리케이션 생성용)
import pandas as pd  # pandas 라이브러리 import (데이터프레임 및 데이터 처리용)
from pymongo import MongoClient  # MongoDB와 연결하기 위한 라이브러리 import

# MongoDB 연결 설정
mongo_client = MongoClient(host="localhost", port=27017)  # 로컬 MongoDB 서버에 연결
db = mongo_client["NewsProject"]  # "NewsProject"라는 이름의 데이터베이스 선택
collection = db["NewsAnalysisDate"]  # "NewsAnalysisDate"라는 이름의 컬렉션 선택

# MongoDB에서 모든 데이터 가져오기
data = list(collection.find())  # MongoDB 컬렉션의 모든 데이터를 리스트로 변환

sentiments = []
for item in data: 
    sentiments.extend(item["sentiment"]) 

# 감성 데이터를 Pandas 데이터프레임으로 변환
df = pd.DataFrame(sentiments)  

# 데이터프레임의 'seendate' 열을 날짜 형식으로 변환
df['seendate'] = pd.to_datetime(df['seendate'])  

# Streamlit 애플리케이션 제목 설정
st.title("기업별 날짜에 따른 감성 지수 변화")  

# 사용자로부터 선택할 기업 옵션을 드롭다운으로 제공
organization = st.selectbox("기업을 선택하세요.", ['Microsoft', 'Google'])  

# 선택된 기업의 데이터만 필터링 / 날짜를 인덱스로 설정
selected_df = df.loc[df['organization'] == organization].set_index('seendate')  

# 긍정(positive), 부정(negative), 중립(neutral) 감성 지수를 선 그래프로 표시
st.line_chart(selected_df[['positive', 'negative', 'neutral']])  

