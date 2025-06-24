from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from sentence_transformers import SentenceTransformer, util
import requests
from typing import TypedDict, List, Optional

from agents.fetchers.news_fetcher import fetch_news_topics
from agents.insight_agent import generate_insights_for_topic
from agents.openai_agent import create_story_from_news, extract_structured_events
from storage.chroma_db import add_document, get_documents

# Init services
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Define State Schema
class NewsState(TypedDict):
    user_input: str
    keywords: List[str]
    news_articles: Optional[List[dict]]
    filtered_articles: Optional[List[dict]]
    summarised_news: Optional[List[dict]]
    stories: Optional[str]

# --- NODE 1: Keyword Extractor ---
def extract_keywords_node(state: NewsState) -> NewsState:
    print("***********Extracting Keywords Node***********")
    print(f"Extracting keywords from user input: {state['user_input']}")
    keywords = extract_structured_events(state["user_input"])
    return {**state, "keywords":  keywords}

# --- NODE 2: News Fetcher ---
def fetch_news_node(state: NewsState) -> NewsState:
    print("***********Fetching News Node***********")
    print(f'Fetching news articles for keywords: {state["keywords"]}')

    fetch_news_topics(state["keywords"])

    documents, metadatas = get_documents(category="news")

    news_articles = []
    for doc, meta in zip(documents[0], metadatas[0]):
        news_articles.append({
            "title": meta.get("title", "Untitled"),
            "url": meta.get("url", ""),
            "text": doc,
            "source": meta.get("source", ""),
        })

    print(f"Fetched {len(news_articles)} news articles.")
    return {**state, "news_articles": news_articles}

# --- NODE 3: Title Matcher ---
def filter_articles_node(state: NewsState) -> NewsState:
    print("***********Filtering Articles Node***********")
    print(f"Filtering articles based on user input: {state['user_input']}")

    try:
        query_keywords = state.get("keywords", [])
        # Step 1: Split and clean keywords
        keywords = [kw.strip() for kw in query_keywords if isinstance(kw, str) and kw.strip()]

        # Step 2: Encode all keyword embeddings
        keyword_embeddings = embedding_model.encode(keywords, convert_to_tensor=True)

        filtered = []

        for article in state["news_articles"]:
            title = article.get("title", "").strip()
            if not title:
                continue

            # Step 3: Encode title
            title_emb = embedding_model.encode(title, convert_to_tensor=True)

            # Step 4: Compute cosine similarity with each keyword embedding
            sims = util.cos_sim(title_emb, keyword_embeddings)
            max_sim = sims.max().item()  # Best match among keywords

            print(f"Max Similarity: {max_sim:.2f} | Title: {title}")

            if max_sim >= 0.4:
                filtered.append((max_sim, article))

        # Step 5: Sort by similarity
        filtered = sorted(filtered, reverse=True)[:15]
        print(f"Filtered down to {len(filtered)} relevant articles based on title similarity.")

        return {**state, "filtered_articles": [article for _, article in filtered]}
    
    except Exception as e:
        print(f"❌ Error during similarity filtering: {e}")
        return {**state, "filtered_articles": []}

# --- NODE 4: Summarizer ---
def summarize_node(state: NewsState) -> NewsState:
    print("***********Summarizing Articles Node***********")
    for article in state["filtered_articles"]:
        generate_insights_for_topic(article["title"], [article["url"]])

    documents, metadatas = get_documents(category="relevant_news")

    stories = []
    for doc, meta in zip(documents[0], metadatas[0]):
        stories.append({
            "title": meta.get("title", ""),
            "urls": meta.get("urls", ""),
            "summary": meta.get("summaries", ""),
            "events": meta.get("events", ""),
        })

    return {**state, "summarised_news": stories}

# --- NODE 5: Story Generator ---
def generate_story_node(state: NewsState) -> NewsState:
    print("***********Generating Story Node***********")
    summarised_articles = state.get("summarised_news", [])

    events = []
    for article in summarised_articles:
        events_text = article.get("events", "")
        if events_text:
            lines = [line.strip() for line in events_text.strip().split("\n") if line.strip()]
            events.extend(lines)

    # Generate story using events
    print(f"Generating story from {len(events)} events.")
    print("Events:", events)
    llm_response = create_story_from_news(events)

    try:
        # Prepare metadata (ensure all values are strings)
        event_str = "\n".join(events)
        source_titles = ", ".join(
            [a.get("title", "") for a in summarised_articles if a.get("title")]
        )

        add_document(
            category="news_stories",
            document=llm_response,
        )
    except Exception as e:
        print(f"⚠️ Failed to store story: {e}")

    print("Generated story:", llm_response)
    return {**state, "stories": llm_response}

# --- Graph Construction ---
graph = StateGraph(NewsState)

graph.add_node("extract_keywords", RunnableLambda(extract_keywords_node))
graph.add_node("fetch_news", RunnableLambda(fetch_news_node))
graph.add_node("filter_articles", RunnableLambda(filter_articles_node))
graph.add_node("summarize", RunnableLambda(summarize_node))
graph.add_node("generate_story", RunnableLambda(generate_story_node))

graph.set_entry_point("extract_keywords")
graph.add_edge("extract_keywords", "fetch_news")
graph.add_edge("fetch_news", "filter_articles" )
graph.add_edge("filter_articles", "summarize")
graph.add_edge("summarize", "generate_story")
graph.add_edge("generate_story", END)

news_chain = graph.compile()

def get_news_chain_object():
    """Returns the compiled news processing chain."""
    return news_chain