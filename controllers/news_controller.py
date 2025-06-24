import chromadb
from agents.fetch_agent import get_news_chain_object
from storage.chroma_db import get_documents, showcollectioncount


class NewsController:

    def __init__(self):
        self.db_client = chromadb.HttpClient(host="localhost", port=8000)


    def get_documents(self, category):
        try:
            print(f"Fetching documents for category: {category}")
            return get_documents(category)
        except Exception as e:
            return [], [{"error": str(e)}]
        
    def get_documents_count(self):
        try:
            info = showcollectioncount()
            return info
        except Exception as e:
            return [], [{"error": str(e)}]
    
    def fetch_story(self, user_input):
        try:
            # Placeholder for actual story fetching logic
            # This should call the appropriate agent or service to fetch stories
            news_chain = get_news_chain_object()
            news_chain.invoke({"user_input": user_input})

            return f"Success: {user_input}"
        except Exception as e:
            return f"Error fetching story: {str(e)}"