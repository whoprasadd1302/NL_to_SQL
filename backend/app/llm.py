import requests
import json
from typing import Generator, List, Dict, Optional

from .config import OLLAMA_BASE_URL, LLM_MODEL

_BASE_SYSTEM_PROMPT = (
    "You are MitraAI (मित्र AI), an intelligent, helpful multilingual conversational AI assistant with deep expertise in Natural Language to SQL (NL-to-SQL) analysis.\n\n"
    "STRICT RESPONSE RULES:\n"
    "1. For ANY question that involves retrieving, listing, counting, filtering, or aggregating data from the database:\n"
    "   a. First output ONLY the SQL query enclosed in a ```sql ... ``` code block. No preamble before the code block.\n"
    "   b. After the code block, write a single concise sentence summarising what the query does or what the result means.\n"
    "   c. Do NOT write any text before the ```sql block for data questions.\n"
    "   d. Do NOT include placeholder commentary like 'Here is the query' or 'I hope this helps'.\n"
    "2. For non-data general questions, respond naturally and helpfully in markdown.\n"
    "3. Use markdown formatting (bold, lists, code) where it improves clarity.\n"
    "4. Maintain conversation context across turns.\n"
    "5. Keep responses concise and to the point."
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
    elif "hinglish" in target_language.lower():
        return (
            "CRITICAL LANGUAGE INSTRUCTION: You MUST respond in conversational Hinglish (Hindi words written in English / Roman alphabet, e.g. 'Namaste! Main aapki help kar sakta hoon. Aapko kya jaanna hai?')."
        )
    elif target_language == "Hindi" or "हिंदी" in target_language:
        return (
            "CRITICAL LANGUAGE INSTRUCTION: You MUST respond exclusively in authentic, fluent Hindi written in Devanagari script (हिंदी देवनागरी लिपि). Do NOT respond in English or Romanized script."
        )
    elif target_language == "Marathi" or "मराठी" in target_language:
        return (
            "CRITICAL LANGUAGE INSTRUCTION: You MUST respond exclusively in authentic, fluent Marathi written in Devanagari script (मराठी देवनागरी लिपी). Use appropriate Marathi vocabulary and respectful tone (उदा. नमस्कार, नक्कीच, मदत)."
        )
    else:
        return f"CRITICAL LANGUAGE INSTRUCTION: You MUST respond strictly in {target_language}."



def _build_ollama_messages(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    target_language: Optional[str] = "Auto-Detect",
    schema_context: Optional[str] = None
) -> List[Dict[str, str]]:
    """Builds messages list with dynamic language instructions, database schema context, and multi-turn context."""
    lang_instruction = _get_language_instruction(target_language)
    
    schema_section = ""
    if schema_context and schema_context.strip():
        schema_section = (
            f"\n\n--- CONNECTED DATABASE SCHEMA ---\n{schema_context}\n---------------------------------\n"
            "IMPORTANT: Use ONLY the tables and columns defined above when writing SQL queries.\n"
            "Write valid SQL SELECT queries for the connected database (PostgreSQL/SQL). The system will auto-execute your SQL query and display results as a table to the user.\n"
            "Always wrap the query in ```sql ... ``` fences."
        )

    system_prompt = f"{_BASE_SYSTEM_PROMPT}\n4. {lang_instruction}{schema_section}"

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
    target_language: Optional[str] = "Auto-Detect",
    schema_context: Optional[str] = None
) -> str:
    """Non-streaming: returns full response adhering to chosen target language and database schema."""
    url = f"{OLLAMA_BASE_URL}/api/chat"

    payload = {
        "model": LLM_MODEL,
        "messages": _build_ollama_messages(user_message, history, target_language, schema_context),
        "stream": False,
        "think": False,
    }

    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]


def stream_response(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    target_language: Optional[str] = "Auto-Detect",
    schema_context: Optional[str] = None
) -> Generator[str, None, None]:
    """Streaming: yields individual tokens adhering to chosen target language and database schema."""
    url = f"{OLLAMA_BASE_URL}/api/chat"

    payload = {
        "model": LLM_MODEL,
        "messages": _build_ollama_messages(user_message, history, target_language, schema_context),
        "stream": True,
        "think": False,
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