import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import re
import nltk
from agents.openai_agent import extract_structured_events
from storage.chroma_db import add_document

nltk.download("punkt")
nltk.download("stopwords")
nltk.download('punkt_tab')
from nltk.tokenize import sent_tokenize

summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def extract_article_from_url(url):
    print(url)
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])
        return text.strip()
    except Exception as e:
        print(f"Failed to extract from {url}: {e}")
        return ""

def chunk_text(text, max_tokens=512):
    sentences = sent_tokenize(text)
    chunks, current_chunk = [], ""
    for sentence in sentences:
        if len((current_chunk + sentence).split()) <= max_tokens:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks


def deduplicate_articles(articles):
    unique_articles = []
    seen = set()
    for article in articles:
        norm_article = re.sub(r"\W", "", article.lower())
        if norm_article not in seen:
            seen.add(norm_article)
            unique_articles.append(article)
    return unique_articles


def summarize_article(article):
    chunks = chunk_text(article)
    summaries = [summarizer(chunk, max_length=130, min_length=30, do_sample=False)[0]["summary_text"] for chunk in chunks]
    return " ".join(summaries)


def build_insight_pipeline(url):
    print(f"Building insight pipeline for URL: {url}")
    raw_articles = [extract_article_from_url(url)]

    deduped_articles = deduplicate_articles(raw_articles)
    article_insights = []

    for article in deduped_articles:
        summary = summarize_article(article)
        events = extract_structured_events(article)

        article_insights.append({
            "url": url,
            "summary": summary,
            "events": events,
        })

    return article_insights


def generate_insights_for_topic(topic, url_string):
    try:
        print(f"🔍 Generating insights for topic: {topic}")
        if isinstance(url_string, list):
            if len(url_string) == 1:
                url_list = [url.strip() for url in url_string[0].split(",") if url.strip()]
            else:
                url_list = url_string  # already a list of URLs
        else:
            url_list = [url.strip() for url in url_string.split(",") if url.strip()]
        summaries = []
        events = []

        for url in url_list:
            try:
                insights = build_insight_pipeline(url)
                
                summaries.append(insights["summary"])
                events.append(insights["events"])
            except Exception as e:
                print(f"⚠️ Failed to process URL {url}: {e}")

        document = {
            "title": topic,
            "urls": ",".join(url_list),
            "summaries": "\n".join(summaries),
            "events": "\n".join(summaries),
        }

        print(f"📄 Document for '{topic}': {document}")
    
        add_document(category="news_insights", document=document)
        print(f"✅ Document for '{topic}' added successfully.")
    except Exception as e:
        print(f"❌ Failed to add document to 'relevant_news' collection: {e}")
