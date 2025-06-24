# 🧠 InsightCrafter: AI-Powered News Summarization & Story Generator

InsightCrafter is an agentic AI pipeline that ingests real-time news, extracts key events, generates structured summaries, and crafts compelling narratives using LLMs. Built for content creators, researchers, and anyone who wants to quickly understand the evolving story behind the headlines.

---

## 🚀 Features

- 📥 Ingest news from news APIs like media stack or news api
- 🧠 Extract structured events from articles using LLMs
- 🗝️ Generate keywords and do similarity-based filtering
- ✍️ Create human-like narratives from news clusters
- 🗂️ Store documents in ChromaDB for retrieval
- 🔍 Query historical or relevant stories
- 💬 Chat-based UI powered by Streamlit


---

# ⚙️ InsightCrafter Setup Guide

This guide walks you through installing and running InsightCrafter — an AI-powered news summarizer and story generator.

---

## 📦 1. Clone the Repository

```bash
git clone https://github.com/your-username/insightcrafter.git
cd insightcrafter
```

---

## 🐍 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate      # On macOS/Linux
venv\Scripts\activate         # On Windows
```

---

## 📚 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔐 4. Add API Keys

Create a `.env` file in the root directory and add your credentials:

```env
NEWS_API_KEY=your_newsapi_key
OPENAI_API_KEY=your_openai_key
```

Replace the placeholder values with your actual API keys.

---

## 🧠 5. Run the App

```bash
streamlit run ui/app.py
```

Once it starts, visit [http://localhost:8501](http://localhost:8501) to use the chat interface.

---

## 🧪 6. Troubleshooting

- **Missing `.env`** → App won't authenticate or fetch news
- **Port already in use** → Run `streamlit run ui/app.py --server.port 8502`
- **Embedding model issues** → Make sure you're online when running for the first time
- **Vector DB not persisting** → Use a persistent ChromaDB setup if needed

---

## ✅ You're Ready to Go!

Explore news topics, generate summaries, and craft stories — all with LLM power.
