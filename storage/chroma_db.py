import hashlib
import chromadb
from datetime import datetime


# ✅ Initialize ChromaDB client using new API format
client = chromadb.HttpClient(host="localhost", port=8000)

# ✅ Create/get collections by category
collections = {
    "news": client.get_or_create_collection("news_articles"),
    "news_insights": client.get_or_create_collection("news_insights"),
    "news_stories": client.get_or_create_collection("news_stories"),
}

def showcollectioncount():
    print("✅ Collections initialized:")
    info = []

    for name, col in collections.items():
        print(f"\n📁 Collection: {col.name}")
        print(f"Total Documents: {col.count()}")
        info.append({
            "name": col.name,
            "total_documents": col.count()
        })
    return info


def showCollections():
    print("✅ Collections initialized:")
    for name, col in collections.items():
        print(f"\n📁 Collection: {col.name}")
        print(f"Total Documents: {col.count()}")

        # Fetch all documents (you can limit with limit=10 if needed)
        data = col.get()

        documents = data.get("documents", [])
        metadatas = data.get("metadatas", [])
        ids = data.get("ids", [])

        for i in range(len(documents)):
            print(f"\n🆔 ID: {ids[i]}")
            print(f"📄 Document: {documents[i]}")
            print(f"🧾 Metadata: {metadatas[i]}")
            print("-" * 50)


showcollectioncount()

def clear_youtube_collection():
    """
    Deletes the YouTube collection from ChromaDB.
    """
    try:
        youtube_collection = collections.get("youtube")
        if youtube_collection:
            print("🧹 Clearing all documents in YouTube collection...")
            youtube_collection.delete(where={})  # Delete all documents
            print("✅ All documents deleted from YouTube collection.")
        else:
            print("⚠️ 'youtube' collection not found in the collections dictionary.")
    except Exception as e:
        print(f"❌ Error while clearing YouTube collection: {e}")


def generate_id_from_url(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def add_document(category: str, document: dict):
    print("Adding document to ChromaDB collection...", category)
    """
    Add a document to the appropriate ChromaDB collection.
    Automatically includes date_inserted in metadata.
    """
    try:
        if category not in collections:
            raise ValueError(f"Unknown category: {category}")

        collection = collections[category]
        doc_id = generate_id_from_url(document["title"])
        today = datetime.now().strftime("%Y-%m-%d")

        # 📌 Common metadata
        metadata = {"date_inserted": today}
        content = ""

        if category == "news_stories":
                metadata.update({
                    "title": document.get("title", "AI-generated story"),
                    "events": document.get("events", ""),
                    "generated_story": document.get("story", ""),
                })
                content = document.get("story", document.get("events", ""))

        elif category == "news_insights":
            urls = document.get("urls", [])
            if isinstance(urls, list):
                urls = ", ".join(urls)
            metadata.update({
                "title": document.get("title", ""),
                "urls": urls,
                "summaries": document.get("summaries", []),
                "events": document.get("events", []),
            })
            content = content = document.get("title", urls)

        elif category == "news":
            metadata.update({
                "title": document.get("title", ""),
                "description": document.get("description", ""),
                "url": document.get("url", ""),
            })
            content = document.get("title", "")

        # 🧠 Store in ChromaDB
        collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )

        print(f"✅ Document successfully added to '{category}' with ID: {doc_id}")

    except Exception as e:
        print(f"❌ Failed to add document to '{category}' collection: {e}")


def get_documents(category):
    if category not in collections:
        raise ValueError(f"Unknown category: {category}")
    results = collections[category].query(query_texts=["*"])
    return results["documents"], results["metadatas"]

