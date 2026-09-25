"""
sql_engine.py
-------------
NL → SQL generation engine for MitraAI.

Responsibilities:
- Build multilingual few-shot prompts (English / Hindi / Marathi / Hinglish)
- Call the Ollama LLM (via llm.py connector) for SQL generation
- Streaming and non-streaming SQL generation
- Extract clean SQL from LLM response (strip markdown fences, prose, etc.)
"""

import re
import json
import logging
import requests
from typing import AsyncGenerator, Dict, Generator, List, Optional

from .config import OLLAMA_BASE_URL, LLM_MODEL

logger = logging.getLogger("mitraai.sql_engine")

# ---------------------------------------------------------------------------
# Supported language identifiers (mirrors llm.py / frontend choices)
# ---------------------------------------------------------------------------
LANG_ENGLISH = "English"
LANG_HINDI = "Hindi"
LANG_MARATHI = "Marathi"
LANG_HINGLISH = "Hinglish"
LANG_AUTO = "Auto-Detect"


# ---------------------------------------------------------------------------
# System prompts per language
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_EN = """\
You are an expert SQLite SQL generator for a banking database.
Your ONLY output must be a single, valid, executable SQL query — nothing else.
Do NOT include explanations, markdown fences, comments, or multiple queries.
The SQL must be compatible with SQLite syntax.
Always use table aliases when joining multiple tables.
Use proper JOIN conditions based on foreign keys provided in the schema.
""".strip()

_SYSTEM_PROMPT_HI = """\
आप एक बैंकिंग डेटाबेस के लिए SQLite SQL जनरेटर हैं।
आपका OUTPUT केवल एक मान्य SQL query होना चाहिए — कुछ और नहीं।
कोई explanation, markdown, या comment न दें।
SQL केवल SQLite syntax में हो।
JOIN करते समय foreign key का उपयोग करें।
""".strip()

_SYSTEM_PROMPT_MR = """\
तुम्ही एक बँकिंग डेटाबेससाठी SQLite SQL generator आहात।
तुमचा OUTPUT फक्त एकच वैध SQL query असावा — इतर काहीही नाही।
explanation, markdown, किंवा comment देऊ नका।
SQL फक्त SQLite syntax मध्ये असावा।
JOIN करताना foreign key चा वापर करा।
""".strip()

_SYSTEM_PROMPT_HINGLISH = """\
Aap ek banking database ke liye SQLite SQL generator ho.
Sirf ek valid SQL query output karo — kuch aur nahi.
Koi explanation, markdown fence, ya comment mat do.
SQL sirf SQLite syntax mein hona chahiye.
JOIN karte waqt foreign key use karo.
""".strip()

_SYSTEM_PROMPT_AUTO = _SYSTEM_PROMPT_EN  # Default to English for SQL generation


# ---------------------------------------------------------------------------
# Few-shot examples per language
# ---------------------------------------------------------------------------

_FEW_SHOT_EN = [
    {
        "user": "Show all customers from Mumbai",
        "sql": "SELECT * FROM customers WHERE city = 'Mumbai';",
    },
    {
        "user": "What is the total balance of all savings accounts?",
        "sql": "SELECT SUM(balance) AS total_savings FROM accounts WHERE account_type = 'Savings';",
    },
    {
        "user": "List customers who have an active loan along with their loan amounts",
        "sql": (
            "SELECT c.name, l.loan_amount, l.loan_type "
            "FROM customers c "
            "JOIN loans l ON c.id = l.cust_id "
            "WHERE l.status = 'Active';"
        ),
    },
]

_FEW_SHOT_HI = [
    {
        "user": "मुंबई के सभी ग्राहक दिखाओ",
        "sql": "SELECT * FROM customers WHERE city = 'Mumbai';",
    },
    {
        "user": "सभी Savings खातों की कुल balance कितनी है?",
        "sql": "SELECT SUM(balance) AS total_savings FROM accounts WHERE account_type = 'Savings';",
    },
    {
        "user": "उन ग्राहकों की सूची बनाओ जिनका loan Approved है और उनकी loan राशि बताओ",
        "sql": (
            "SELECT c.name, l.loan_amount, l.loan_type "
            "FROM customers c "
            "JOIN loans l ON c.id = l.cust_id "
            "WHERE l.status = 'Approved';"
        ),
    },
]

_FEW_SHOT_MR = [
    {
        "user": "मुंबईतील सर्व ग्राहक दाखवा",
        "sql": "SELECT * FROM customers WHERE city = 'Mumbai';",
    },
    {
        "user": "सर्व Savings खात्यांची एकूण शिल्लक किती आहे?",
        "sql": "SELECT SUM(balance) AS total_savings FROM accounts WHERE account_type = 'Savings';",
    },
    {
        "user": "ज्या ग्राहकांचे कर्ज Approved आहे त्यांची नावे आणि कर्जाची रक्कम दाखवा",
        "sql": (
            "SELECT c.name, l.loan_amount, l.loan_type "
            "FROM customers c "
            "JOIN loans l ON c.id = l.cust_id "
            "WHERE l.status = 'Approved';"
        ),
    },
]

_FEW_SHOT_HINGLISH = [
    {
        "user": "Mumbai ke saare customers dikhao",
        "sql": "SELECT * FROM customers WHERE city = 'Mumbai';",
    },
    {
        "user": "Sabhi savings accounts ka total balance kya hai?",
        "sql": "SELECT SUM(balance) AS total_savings FROM accounts WHERE account_type = 'Savings';",
    },
    {
        "user": "Un customers ki list banao jinke loan active hain aur unka loan amount bhi batao",
        "sql": (
            "SELECT c.name, l.loan_amount, l.loan_type "
            "FROM customers c "
            "JOIN loans l ON c.id = l.cust_id "
            "WHERE l.status = 'Active';"
        ),
    },
]

# Map language names to (system_prompt, few_shot_examples)
_LANG_CONFIG: Dict[str, tuple] = {
    LANG_ENGLISH: (_SYSTEM_PROMPT_EN, _FEW_SHOT_EN),
    LANG_HINDI: (_SYSTEM_PROMPT_HI, _FEW_SHOT_HI),
    LANG_MARATHI: (_SYSTEM_PROMPT_MR, _FEW_SHOT_MR),
    LANG_HINGLISH: (_SYSTEM_PROMPT_HINGLISH, _FEW_SHOT_HINGLISH),
    LANG_AUTO: (_SYSTEM_PROMPT_AUTO, _FEW_SHOT_EN),
}

# Hindi/Marathi aliases to match frontend strings like "Hindi (हिंदी)"
_LANG_ALIASES = {
    "हिंदी": LANG_HINDI,
    "मराठी": LANG_MARATHI,
}


def _normalize_language(language: Optional[str]) -> str:
    """Normalise free-form language strings to one of the known LANG_* constants."""
    if not language:
        return LANG_AUTO
    for fragment, canonical in _LANG_ALIASES.items():
        if fragment in language:
            return canonical
    return language if language in _LANG_CONFIG else LANG_AUTO


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_sql_prompt(
    query: str,
    schema: str,
    language: Optional[str] = LANG_ENGLISH,
    history: Optional[List[Dict[str, str]]] = None,
) -> List[Dict[str, str]]:
    """
    Builds a list of Ollama-compatible chat messages for SQL generation.

    Args:
        query:    The natural-language question from the user.
        schema:   The formatted schema string from schema_manager.get_schema_context().
        language: Target language (English / Hindi / Marathi / Hinglish / Auto-Detect).
        history:  Optional prior conversation turns [{"role": ..., "content": ...}].

    Returns:
        List of message dicts suitable for the Ollama /api/chat payload.
    """
    lang = _normalize_language(language)
    system_prompt, few_shots = _LANG_CONFIG.get(lang, _LANG_CONFIG[LANG_AUTO])

    # Build the system message, embedding the schema
    full_system = (
        f"{system_prompt}\n\n"
        f"Database Schema:\n{schema}"
    )
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": full_system}
    ]

    # Inject few-shot examples as alternating user/assistant turns
    for example in few_shots:
        messages.append({"role": "user", "content": example["user"]})
        messages.append({"role": "assistant", "content": example["sql"]})

    # Append any prior conversation context (last 6 turns to stay concise)
    if history:
        for msg in history[-6:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    # Finally, add the current user query
    messages.append({"role": "user", "content": query})
    return messages


def extract_sql(response: str) -> str:
    """
    Extracts a clean SQL statement from a raw LLM response.

    Handles:
    - Markdown fenced code blocks (```sql ... ``` / ``` ... ```)
    - Inline backtick code spans
    - Leading/trailing prose (takes the first complete SQL-looking statement)
    - Trailing semicolon normalisation

    Returns:
        A single, stripped SQL string. Empty string if nothing found.
    """
    text = response.strip()

    # 1. Try to extract from fenced code block
    fence_match = re.search(
        r"```(?:sql|SQL)?\s*\n?(.*?)```",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if fence_match:
        return fence_match.group(1).strip()

    # 2. Try inline backtick span
    inline_match = re.search(r"`([^`]+)`", text)
    if inline_match:
        candidate = inline_match.group(1).strip()
        if _looks_like_sql(candidate):
            return candidate

    # 3. Find first line that begins with a known SQL keyword
    sql_keywords = (
        "SELECT", "INSERT", "UPDATE", "DELETE", "WITH",
        "CREATE", "DROP", "ALTER", "EXPLAIN",
    )
    lines = text.splitlines()
    sql_lines: List[str] = []
    collecting = False
    for line in lines:
        stripped = line.strip()
        if not collecting and any(stripped.upper().startswith(kw) for kw in sql_keywords):
            collecting = True
        if collecting:
            sql_lines.append(line)
            # Stop collecting at a blank line after we have content
            if not stripped and sql_lines:
                break

    if sql_lines:
        return "\n".join(sql_lines).strip()

    # 4. Last resort: return the whole stripped response
    return text


def _looks_like_sql(text: str) -> bool:
    """Heuristic: does the string contain SQL keywords?"""
    sql_keywords = {"SELECT", "INSERT", "UPDATE", "DELETE", "FROM", "WHERE", "JOIN"}
    upper = text.upper()
    return any(kw in upper for kw in sql_keywords)


def generate_sql(
    query: str,
    schema: str,
    language: Optional[str] = LANG_ENGLISH,
    history: Optional[List[Dict[str, str]]] = None,
    model: Optional[str] = None,
) -> str:
    """
    Non-streaming SQL generation.

    Calls Ollama /api/chat (stream=False), returns the extracted SQL string.

    Args:
        query:    Natural-language question.
        schema:   Formatted schema string from schema_manager.
        language: Output language hint for the system prompt.
        history:  Optional prior conversation turns.
        model:    Ollama model name (defaults to LLM_MODEL from config).

    Returns:
        Extracted SQL string.

    Raises:
        requests.HTTPError on API failure.
        RuntimeError if the response is missing expected fields.
    """
    model = model or LLM_MODEL
    messages = build_sql_prompt(query, schema, language, history)
    url = f"{OLLAMA_BASE_URL}/api/chat"

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()

    data = resp.json()
    raw_content = data.get("message", {}).get("content", "")
    if not raw_content:
        raise RuntimeError(f"Ollama returned empty content. Full response: {data}")

    sql = extract_sql(raw_content)
    logger.info("generate_sql [%s]: %s -> %s", language, query[:60], sql[:80])
    return sql


def generate_sql_stream(
    query: str,
    schema: str,
    language: Optional[str] = LANG_ENGLISH,
    history: Optional[List[Dict[str, str]]] = None,
    model: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Synchronous streaming SQL generation (yields raw tokens from Ollama).

    Yields individual text tokens as they arrive from the LLM.
    The caller is responsible for accumulating tokens and calling extract_sql()
    on the full accumulated string.

    Args:
        query:    Natural-language question.
        schema:   Formatted schema string from schema_manager.
        language: Output language hint for the system prompt.
        history:  Optional prior conversation turns.
        model:    Ollama model name (defaults to LLM_MODEL from config).

    Yields:
        str — individual token strings.

    Raises:
        requests.HTTPError on API failure.
    """
    model = model or LLM_MODEL
    messages = build_sql_prompt(query, schema, language, history)
    url = f"{OLLAMA_BASE_URL}/api/chat"

    payload = {
        "model": model,
        "messages": messages,
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


async def generate_sql_stream_async(
    query: str,
    schema: str,
    language: Optional[str] = LANG_ENGLISH,
    history: Optional[List[Dict[str, str]]] = None,
    model: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Async wrapper around generate_sql_stream for use with FastAPI StreamingResponse.

    Yields individual token strings asynchronously.
    """
    # Run the synchronous generator in-place — suitable for I/O-bound Ollama calls
    # For true async, replace with httpx.AsyncClient; this keeps parity with llm.py.
    for token in generate_sql_stream(query, schema, language, history, model):
        yield token
