import requests

from .config import OLLAMA_BASE_URL, LLM_MODEL


def generate_response(user_message: str) -> str:
    url = f"{OLLAMA_BASE_URL}/api/chat"

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are MitraAI, a helpful multilingual "
                    "conversational assistant. "
                    "Understand the user's language and respond "
                    "in the same language. "
                    "Give clear, accurate and concise answers."
                ),
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        "stream": False,
    }

    response = requests.post(
        url,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"]