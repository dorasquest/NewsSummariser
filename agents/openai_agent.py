import os
from openai import AzureOpenAI

from storage.chroma_db import add_document

# Configure Azure OpenAI client
endpoint = os.getenv("ENDPOINT_URL", "https://youtubevideosstorygen.openai.azure.com/")
deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4o")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY", "REPLACE_WITH_YOUR_KEY_VALUE_HERE")

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=subscription_key,
    api_version="2025-01-01-preview",
)



def create_story_from_news(events):

    # Format story input
    story_input = "Here are recent news developments:\n\n"
    story_input += f"🔹 {events}\n\n"

    # LLM prompt
    prompt = [
        {
            "role": "system",
            "content": (
                "You are a storytelling assistant that turns news summaries into an engaging story or narrative.\n"
                "Use a narrative tone, connect themes, and present it as a brief 3-paragraph story."
            )
        },
        {
            "role": "user",
            "content": story_input
        }
    ]

    # Call Azure LLM
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt,
        temperature=0.7,
        max_tokens=800
    )

    story = response.choices[0].message.content.strip()

    add_document(
        category="news_stories",
        document={
            "title": "AI-generated story",
            "events": events,
            "story": story
        }
    )

    return story

def extract_structured_events(text: str) -> str:
    """Takes raw news text and returns extracted key events using Azure GPT-4o."""
    
    # Thresholds — tweak as needed
    word_count = len(text.strip().split())
    mode = "keyword" if word_count < 50 else "event"

    if mode == "keyword":
        task_instruction = (
            "Generate 3 to 5 keywords or phrases that capture the core topic of the following query. "
            "Return them as a comma-separated list.\n\n"
            f"Query: {text}"
        )
    else:
        task_instruction = (
            "Extract 3 to 5 key events from the following news article. Each event should follow this format:\n"
            "[Actor] performed [Action] on [Date] at [Location], due to [Reason].\n\n"
            f"Article: {text}"
        )

    chat_prompt = [
        {"role": "system", "content": "You are an AI assistant that follows instructions precisely."},
        {"role": "user", "content": task_instruction}
    ]


    try:
        completion = client.chat.completions.create(
            model=deployment,
            messages=chat_prompt,
            max_tokens=800,
            temperature=0.7,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stream=False
        )

        return completion.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"❌ Error extracting structured events: {e}")
        return ""
