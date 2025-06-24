import os
from datetime import datetime, timedelta
from typing import List
from dataclasses import dataclass
import requests
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, util

from storage.chroma_db import add_document

# Setup
load_dotenv()

# Constants
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
MEDIA_STACK_API_KEY = os.getenv("MEDIA_STACK_API_KEY")
DEFAULT_COUNTRY = "us"
SIMILARITY_TOP_K = 30

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')


@dataclass
class NewsArticle:
    title: str
    description: str
    url: str


def fetch_from_mediastack(
    keywords: str,
    country: str = DEFAULT_COUNTRY
) -> List[NewsArticle]:
    """Fetch articles from MediaStack API."""
    url = "https://api.mediastack.com/v1/news"
    params = {
        "access_key": MEDIA_STACK_API_KEY,
        "keywords": keywords,
        "countries": country,
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"MediaStack API error:{response.status_code} - {response.text}")
        return []

    articles = response.json().get("data", [])
    print(
        f"MediaStack returned {len(articles)} articles for keyword: {keywords}"
        )

    return [
        NewsArticle(
            title=a.get("title", ""),
            description=a.get("description", ""),
            url=a.get("url", "")
        ) for a in articles
    ]


def fetch_from_newsapi(
        keywords: str
        ) -> List[NewsArticle]:
    """Fetch articles from NewsAPI with date fallback."""

    dt_obj = datetime.now()
    from_date = (dt_obj - timedelta(days=1)).strftime("%Y-%m-%d")
    formatted_query = "+".join(keywords.split())

    search_in = "title,description,content"
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": formatted_query,
        "from": from_date,
        "apiKey": NEWS_API_KEY,
        "searchIn": search_in,
        "from": from_date,
        "to": dt_obj.strftime("%Y-%m-%d"),
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 20,
        "page": 1,
    }
    
    print(f"Fetching articles from NewsAPI for keywords: {formatted_query}")
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"NewsAPI error: {response.status_code} - {response.text}")
        return []

    articles = response.json().get("articles", [])
    print(f"NewsAPI returned {len(articles)} articles for keyword: {keywords}")

    return [
        NewsArticle(
            title=a.get("title", ""),
            description=a.get("description", ""),
            url=a.get("url", "")
        ) for a in articles
    ]


def fetch_news_articles(keywords: str, date: str) -> List[NewsArticle]:
    """Try MediaStack first, fallback to NewsAPI."""
    articles = fetch_from_newsapi(keywords)
    if articles:
        return articles
    return fetch_from_mediastack(keywords, date)


def filter_relevant_articles(
        keywords: str, articles: List[NewsArticle]
        ) -> List[NewsArticle]:
    """Filter news articles using semantic similarity to the keyword."""
    print("Filtering articles using semantic similarity...")

    query_embedding = model.encode(keywords, convert_to_tensor=True)
    scored_articles = []

    for article in articles:
        combined_text = f"{article.title} {article.description}"
        article_embedding = model.encode(combined_text, convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(
            query_embedding, article_embedding
        ).item()
        scored_articles.append((similarity, article))

    sorted_articles = sorted(scored_articles, key=lambda x: x[0], reverse=True)
    top_articles = [
        article
        for _, article in sorted_articles[:SIMILARITY_TOP_K]
    ]
    print(f"Selected top {len(top_articles)} relevant articles.")
    return top_articles


def store_news_articles(articles: List[NewsArticle]):
    for article in articles:
        document = article.__dict__.copy()
        document["date_inserted"] = datetime.now().strftime('%Y-%m-%d')

        add_document(category="news", document=document)


def get_news_for_topic(topic: str, date: str) -> List[NewsArticle]:
    """Pipeline: fetch + filter news for a Google Trend topic."""
    print(f"Processing topic: {topic}")
    raw_articles = fetch_news_articles(topic, date)
    store_news_articles(raw_articles)


def fetch_news_topics(news_topics):
    news_topics = [kw.strip() for kw in news_topics.split(",") if kw.strip()]


    topics = news_topics
    today = datetime.now().strftime("%Y-%m-%d")
    for topic in topics:
        try:
            print(f"Topic to fetch news from: {topic}")
            get_news_for_topic(topic, today)
        except Exception as e:
            print(f"❌ Error fetching news for topic '{topic}': {e}")



