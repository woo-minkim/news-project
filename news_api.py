from gdeltdoc import GdeltDoc, Filters 
from newspaper import Article

f = Filters(
    start_date = "2024-05-01",
    end_date = "2024-05-25",
    num_records = 10,
    keyword = "Microsoft",
    domain = "nytimes.com",
    country = "US",
)

gd = GdeltDoc() # GdeltDoc 클래스의 인스턴스 생성, Gdelt 데이터베이스에 접근 가능
articles = gd.article_search(f) # Gdelt 데이터베이스에서 필터를 적용한 기사 검색

# 특정 기사 URL을 사용하여 newspaper3k 라이브러리를 사용하여 기사 내용을 가져옴
url = articles.loc[1, "url"]
print(articles.loc[1, "title"])
print("---------------------")

article = Article(url)
article.download()
article.parse() 
print(article.text)