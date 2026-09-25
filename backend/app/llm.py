import requests
import json
from typing import Generator, List, Dict, Optional

from .config import OLLAMA_BASE_URL, LLM_MODEL

_BASE_SYSTEM_PROMPT = (
    "You are MitraAI (मित्र AI), an intelligent and helpful multilingual conversational AI assistant. "
    "Guidelines:\n"
    "1. Be polite, concise, structured, and helpful. Use markdown formatting when appropriate.\n"
    "2. Maintain conversation context across turns."
)


def _get_language_instruction(target_language: Optional[str]) -> str:
    """Returns specific prompting rules based on the user's selected language."""
    if not target_language or target_language == "Auto-Detect":
        return (
            "Understand the user's intent and language, and respond naturally in the SAME language or script they used."
        )
    elif target_language == "English":
        return (
            "CRITICAL LANGUAGE INSTRUCTION: You MUST respond exclusively in clear, fluent English regardless of the input language."
        )
    elif target_language == "Hindi" or "हिंदी" in target_language:
        return (
            "CRITICAL LANGUAGE INSTRUCTION: You MUST respond exclusively in authentic, fluent Hindi written in Devanagari script (हिंदी देवनागरी लिपि). Do NOT respond in English or Romanized script."
        )
    elif target_language == "Marathi" or "मराठी" in target_language:
        return (
            "CRITICAL LANGUAGE INSTRUCTION: You MUST respond exclusively in authentic, fluent Marathi written in Devanagari script (मराठी देवनागरी लिपी). Use appropriate Marathi vocabulary and respectful tone (उदा. नमस्कार, नक्कीच, मदत)."
        )
    elif target_language == "Hinglish":
        return (
            "CRITICAL LANGUAGE INSTRUCTION: You MUST respond in conversational Hinglish (Hindi words written in English / Roman alphabet, e.g. 'Namaste! Main aapki help kar sakta hoon. Aapko kya jaanna hai?')."
        )
    else:
        return f"CRITICAL LANGUAGE INSTRUCTION: You MUST respond strictly in {target_language}."


def _build_ollama_messages(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    target_language: Optional[str] = "Auto-Detect"
) -> List[Dict[str, str]]:
    """Builds messages list with dynamic language instructions and multi-turn context."""
    lang_instruction = _get_language_instruction(target_language)
    system_prompt = f"{_BASE_SYSTEM_PROMPT}\n3. {lang_instruction}"

    messages = [{"role": "system", "content": system_prompt}]

    if history:
        # Include up to the last 12 messages for context
        recent_history = history[-12:]
        for msg in recent_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ["user", "assistant"] and content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})
    return messages


def generate_response(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    target_language: Optional[str] = "Auto-Detect"
) -> str:
    """Non-streaming: returns full response adhering to chosen target language."""
    url = f"{OLLAMA_BASE_URL}/api/chat"

    payload = {
        "model": LLM_MODEL,
        "messages": _build_ollama_messages(user_message, history, target_language),
        "stream": False,
    }

    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]


def stream_response(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    target_language: Optional[str] = "Auto-Detect"
) -> Generator[str, None, None]:
    """Streaming: yields individual tokens adhering to chosen target language."""
    url = f"{OLLAMA_BASE_URL}/api/chat"

    payload = {
        "model": LLM_MODEL,
        "messages": _build_ollama_messages(user_message, history, target_language),
        "stream": True,
    }

    with requests.post(url, json=payload, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            chunk = line.decode("utf-8") if isinstance(line, bytes) else line
            try:
                data = json.loads(chunk)
            except ValueError:
                continue
            token = data.get("message", {}).get("content", "")
            if token:
                yield token
            if data.get("done"):
                break