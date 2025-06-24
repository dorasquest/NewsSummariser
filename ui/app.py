import streamlit as st
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controllers.news_controller import NewsController


st.set_page_config(page_title="🧠 News Chat Assistant", layout="wide")
st.title("🗞️ AI News Assistant")

# Initialize controller
controller = NewsController()

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown("---")

# --- Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# --- Chat Input ---
if prompt := st.chat_input("Ask about a topic (e.g., Tesla AI, ChatGPT, etc.)"):
    # Show user's message immediately in UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Show spinner and start backend fetch
    with st.chat_message("assistant"):
        with st.spinner("Searching and writing a story..."):
            # Temporarily show "Thinking..." message while response loads
            placeholder = st.empty()
            placeholder.markdown("_Generating response..._")

            try:
                response = controller.fetch_story(prompt)

                # Replace spinner placeholder with actual response
                documents, metadatas = controller.get_documents(category="news_stories")

                if documents and metadatas:
                    latest_doc = documents[0][-1]
                    latest_meta = metadatas[0][-1]

                    story = latest_doc.get("story") or latest_meta.get("generated_story", "")
                    events = latest_meta.get("events", "")

                    if story:
                        st.markdown("### 🧠 Generated Story")
                        st.markdown(story)

                        if events:
                            with st.expander("📌 Events used"):
                                st.markdown(events)

                        st.session_state.messages.append({"role": "assistant", "content": story})
                    else:
                        st.error("⚠️ No story found in the latest document.")

                else:
                    st.error("⚠️ No documents found in news_stories collection.")

            except Exception as e:
                error_msg = f"❌ Something went wrong: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

