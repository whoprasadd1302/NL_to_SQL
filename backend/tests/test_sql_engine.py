"""
test_sql_engine.py
------------------
Unit tests for backend/app/sql_engine.py

Covers:
- build_sql_prompt returns correct structure for EN / HI / MR / Hinglish
- extract_sql strips markdown fences, backticks, and prose
- generate_sql returns valid SQL (mocked Ollama endpoint)
"""

import os
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is on sys.path regardless of how pytest is invoked
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest
from backend.app.sql_engine import (
    build_sql_prompt,
    extract_sql,
    generate_sql,
    generate_sql_stream,
    LANG_ENGLISH,
    LANG_HINDI,
    LANG_MARATHI,
    LANG_HINGLISH,
    LANG_AUTO,
    _normalize_language,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SAMPLE_SCHEMA = (
    "Tables:\n"
    "- customers: id (INT), name (TEXT), city (TEXT), balance (REAL)\n"
    "- accounts: id (INT), cust_id (INT), account_type (TEXT), balance (REAL)\n"
    "- transactions: id (INT), account_id (INT), amount (REAL), transaction_type (TEXT), transaction_date (TEXT)\n"
    "- loans: id (INT), cust_id (INT), loan_amount (REAL), loan_type (TEXT), status (TEXT)\n"
    "Foreign Keys:\n"
    "- accounts.cust_id → customers.id\n"
    "- transactions.account_id → accounts.id\n"
    "- loans.cust_id → customers.id"
)


# ===========================================================================
# build_sql_prompt tests
# ===========================================================================

class TestBuildSqlPrompt:
    """Tests for build_sql_prompt() across all supported languages."""

    def _assert_common_structure(self, messages: list, query: str) -> None:
        """Assert structural requirements common across all languages."""
        assert isinstance(messages, list)
        assert len(messages) >= 3  # system + at least 1 few-shot pair + user query

        # First message must always be the system prompt
        assert messages[0]["role"] == "system"
        system_content = messages[0]["content"]

        # Schema must be embedded in the system message
        assert "Tables:" in system_content
        assert "customers" in system_content
        assert "Foreign Keys:" in system_content

        # Last message must be the actual user query
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == query

        # Verify alternating few-shot structure (after system, before final user)
        for i, msg in enumerate(messages[1:-1]):
            assert msg["role"] in ("user", "assistant")
            assert msg["content"]  # non-empty

    def test_english_prompt_structure(self):
        """build_sql_prompt returns correct prompt for English."""
        query = "Show all customers from Mumbai"
        messages = build_sql_prompt(query, SAMPLE_SCHEMA, LANG_ENGLISH)

        self._assert_common_structure(messages, query)

        # English system prompt keywords
        system = messages[0]["content"]
        assert "SQL" in system
        assert "SQLite" in system

        # English few-shot examples present
        all_content = " ".join(m["content"] for m in messages)
        assert "Mumbai" in all_content  # from few-shot or query
        assert "SELECT" in all_content.upper()

    def test_hindi_prompt_structure(self):
        """build_sql_prompt returns correct prompt for Hindi (हिंदी)."""
        query = "मुंबई के सभी ग्राहक दिखाओ"
        messages = build_sql_prompt(query, SAMPLE_SCHEMA, LANG_HINDI)

        self._assert_common_structure(messages, query)

        system = messages[0]["content"]
        # Hindi system prompt should contain Devanagari text
        assert "SQL" in system
        # Hindi language instruction present
        assert any(
            c > "\u0900"  # Unicode Devanagari block starts at U+0900
            for c in system
        ), "System prompt should contain Devanagari characters for Hindi"

        # Hindi few-shot examples (Devanagari in user turns)
        user_contents = [m["content"] for m in messages if m["role"] == "user"]
        has_devanagari = any(
            any(c > "\u0900" for c in content) for content in user_contents
        )
        assert has_devanagari, "Hindi few-shot examples should contain Devanagari text"

    def test_marathi_prompt_structure(self):
        """build_sql_prompt returns correct prompt for Marathi (मराठी)."""
        query = "मुंबईतील सर्व ग्राहक दाखवा"
        messages = build_sql_prompt(query, SAMPLE_SCHEMA, LANG_MARATHI)

        self._assert_common_structure(messages, query)

        system = messages[0]["content"]
        assert "SQL" in system
        assert any(c > "\u0900" for c in system), (
            "Marathi system prompt should contain Devanagari characters"
        )

    def test_hinglish_prompt_structure(self):
        """build_sql_prompt returns correct prompt for Hinglish."""
        query = "Mumbai ke saare customers dikhao"
        messages = build_sql_prompt(query, SAMPLE_SCHEMA, LANG_HINGLISH)

        self._assert_common_structure(messages, query)

        system = messages[0]["content"]
        # Hinglish prompt is Romanised Hindi — check characteristic words
        assert "SQL" in system

    def test_auto_detect_falls_back_to_english(self):
        """Auto-Detect language falls back to the English prompt."""
        query = "List all loans"
        messages_auto = build_sql_prompt(query, SAMPLE_SCHEMA, LANG_AUTO)
        messages_en = build_sql_prompt(query, SAMPLE_SCHEMA, LANG_ENGLISH)

        # Both should have same system prompt
        assert messages_auto[0]["content"] == messages_en[0]["content"]

    def test_unknown_language_falls_back_to_auto(self):
        """An unknown language string falls back gracefully."""
        query = "Show loans"
        messages = build_sql_prompt(query, SAMPLE_SCHEMA, "Klingon")
        assert messages[0]["role"] == "system"
        assert messages[-1]["content"] == query

    def test_schema_is_embedded_in_system_prompt(self):
        """Schema string is injected into the system prompt message."""
        messages = build_sql_prompt("Any query", SAMPLE_SCHEMA, LANG_ENGLISH)
        system_content = messages[0]["content"]
        assert "- customers:" in system_content
        assert "accounts.cust_id" in system_content

    def test_history_is_appended(self):
        """Prior conversation history is appended between few-shots and user query."""
        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "SELECT * FROM customers;"},
        ]
        query = "New question"
        messages = build_sql_prompt(query, SAMPLE_SCHEMA, LANG_ENGLISH, history=history)

        all_content = [m["content"] for m in messages]
        assert "Previous question" in all_content
        assert "SELECT * FROM customers;" in all_content
        assert messages[-1]["content"] == query

    def test_few_shot_count_english(self):
        """English prompt includes exactly 3 few-shot user/assistant pairs."""
        messages = build_sql_prompt("q", SAMPLE_SCHEMA, LANG_ENGLISH)
        # messages = [system, user, assistant, user, assistant, user, assistant, user(query)]
        # Pairs between index 1 and -1
        few_shot_messages = messages[1:-1]
        user_turns = [m for m in few_shot_messages if m["role"] == "user"]
        asst_turns = [m for m in few_shot_messages if m["role"] == "assistant"]
        assert len(user_turns) == 3
        assert len(asst_turns) == 3

    def test_alias_hindi_devanagari_string(self):
        """Language strings containing 'हिंदी' are mapped to Hindi."""
        lang = "Hindi (हिंदी)"
        messages = build_sql_prompt("q", SAMPLE_SCHEMA, lang)
        system = messages[0]["content"]
        assert any(c > "\u0900" for c in system)

    def test_alias_marathi_devanagari_string(self):
        """Language strings containing 'मराठी' are mapped to Marathi."""
        lang = "Marathi (मराठी)"
        messages = build_sql_prompt("q", SAMPLE_SCHEMA, lang)
        system = messages[0]["content"]
        assert any(c > "\u0900" for c in system)


# ===========================================================================
# extract_sql tests
# ===========================================================================

class TestExtractSql:
    """Tests for extract_sql() — markdown stripping and SQL extraction."""

    def test_plain_sql_passthrough(self):
        """A bare SQL string is returned unchanged."""
        sql = "SELECT * FROM customers WHERE city = 'Mumbai';"
        assert extract_sql(sql) == sql

    def test_strips_sql_markdown_fence(self):
        """Removes ```sql ... ``` fence."""
        response = "```sql\nSELECT * FROM customers;\n```"
        result = extract_sql(response)
        assert result == "SELECT * FROM customers;"
        assert "```" not in result

    def test_strips_plain_markdown_fence(self):
        """Removes ``` ... ``` fence without language tag."""
        response = "```\nSELECT id FROM loans;\n```"
        result = extract_sql(response)
        assert result == "SELECT id FROM loans;"
        assert "```" not in result

    def test_strips_case_insensitive_fence(self):
        """Handles ```SQL (uppercase) fence."""
        response = "```SQL\nSELECT name FROM customers;\n```"
        result = extract_sql(response)
        assert result == "SELECT name FROM customers;"

    def test_strips_leading_prose(self):
        """Ignores explanatory text before the SQL keyword."""
        response = "Here is your SQL query:\nSELECT * FROM accounts;"
        result = extract_sql(response)
        assert "SELECT" in result.upper()
        assert "accounts" in result

    def test_strips_inline_backtick(self):
        """Extracts SQL from inline backtick span."""
        response = "The query is `SELECT id FROM customers;`"
        result = extract_sql(response)
        assert "SELECT" in result.upper()

    def test_multiline_sql_preserved(self):
        """Multi-line SQL is preserved correctly."""
        response = (
            "```sql\n"
            "SELECT c.name, l.loan_amount\n"
            "FROM customers c\n"
            "JOIN loans l ON c.id = l.cust_id\n"
            "WHERE l.status = 'Active';\n"
            "```"
        )
        result = extract_sql(response)
        assert "SELECT" in result
        assert "JOIN" in result
        assert "WHERE" in result
        assert "```" not in result

    def test_empty_response(self):
        """Empty string returns empty string."""
        assert extract_sql("") == ""

    def test_strips_trailing_whitespace(self):
        """Result is always stripped."""
        response = "  SELECT * FROM customers;  \n"
        result = extract_sql(response)
        assert result == result.strip()


# ===========================================================================
# generate_sql tests (Ollama mocked)
# ===========================================================================

def _make_mock_response(sql_text: str):
    """Helper: construct a mock requests.Response for Ollama /api/chat."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "model": "qwen3:8b",
        "message": {"role": "assistant", "content": sql_text},
        "done": True,
    }
    return mock_resp


class TestGenerateSql:
    """Tests for generate_sql() with mocked Ollama."""

    @patch("backend.app.sql_engine.requests.post")
    def test_generate_sql_returns_valid_sql_english(self, mock_post):
        """generate_sql returns cleaned SQL for an English query."""
        expected_sql = "SELECT * FROM customers WHERE city = 'Mumbai';"
        mock_post.return_value = _make_mock_response(expected_sql)

        result = generate_sql(
            query="Show all customers from Mumbai",
            schema=SAMPLE_SCHEMA,
            language=LANG_ENGLISH,
        )

        assert "SELECT" in result.upper()
        assert "customers" in result.lower()
        mock_post.assert_called_once()

    @patch("backend.app.sql_engine.requests.post")
    def test_generate_sql_strips_markdown_from_response(self, mock_post):
        """generate_sql extracts SQL even when LLM wraps it in markdown."""
        raw_response = "```sql\nSELECT SUM(balance) FROM accounts WHERE account_type = 'Savings';\n```"
        mock_post.return_value = _make_mock_response(raw_response)

        result = generate_sql(
            query="Total savings balance",
            schema=SAMPLE_SCHEMA,
            language=LANG_ENGLISH,
        )

        assert "SELECT" in result.upper()
        assert "```" not in result

    @patch("backend.app.sql_engine.requests.post")
    def test_generate_sql_hindi_query(self, mock_post):
        """generate_sql handles a Hindi-language query and returns SQL."""
        expected_sql = "SELECT * FROM customers WHERE city = 'Mumbai';"
        mock_post.return_value = _make_mock_response(expected_sql)

        result = generate_sql(
            query="मुंबई के सभी ग्राहक दिखाओ",
            schema=SAMPLE_SCHEMA,
            language=LANG_HINDI,
        )

        assert "SELECT" in result.upper()
        # Verify the Hindi system prompt was used
        call_args = mock_post.call_args
        payload = call_args[1]["json"] if "json" in call_args[1] else call_args[0][1]
        system_msg = payload["messages"][0]
        assert system_msg["role"] == "system"
        # Hindi system contains Devanagari
        assert any(c > "\u0900" for c in system_msg["content"])

    @patch("backend.app.sql_engine.requests.post")
    def test_generate_sql_marathi_query(self, mock_post):
        """generate_sql handles a Marathi-language query and returns SQL."""
        expected_sql = "SELECT name FROM customers WHERE city = 'Pune';"
        mock_post.return_value = _make_mock_response(expected_sql)

        result = generate_sql(
            query="पुण्यातील ग्राहकांची नावे दाखवा",
            schema=SAMPLE_SCHEMA,
            language=LANG_MARATHI,
        )

        assert "SELECT" in result.upper()

    @patch("backend.app.sql_engine.requests.post")
    def test_generate_sql_uses_correct_model(self, mock_post):
        """generate_sql sends the correct model name in the Ollama payload."""
        mock_post.return_value = _make_mock_response("SELECT 1;")

        generate_sql("test query", SAMPLE_SCHEMA, LANG_ENGLISH, model="qwen3:8b")

        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs.get("json", {})
        assert payload.get("model") == "qwen3:8b"
        assert payload.get("stream") is False

    @patch("backend.app.sql_engine.requests.post")
    def test_generate_sql_raises_on_http_error(self, mock_post):
        """generate_sql propagates HTTPError on non-2xx Ollama response."""
        import requests as req_lib
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req_lib.HTTPError("503 Server Error")
        mock_post.return_value = mock_resp

        with pytest.raises(req_lib.HTTPError):
            generate_sql("query", SAMPLE_SCHEMA, LANG_ENGLISH)

    @patch("backend.app.sql_engine.requests.post")
    def test_generate_sql_raises_on_empty_content(self, mock_post):
        """generate_sql raises RuntimeError when Ollama returns empty content."""
        mock_post.return_value = _make_mock_response("")

        with pytest.raises(RuntimeError, match="empty content"):
            generate_sql("query", SAMPLE_SCHEMA, LANG_ENGLISH)


# ===========================================================================
# generate_sql_stream tests (Ollama mocked)
# ===========================================================================

class TestGenerateSqlStream:
    """Tests for generate_sql_stream() with mocked Ollama."""

    @patch("backend.app.sql_engine.requests.post")
    def test_stream_yields_tokens(self, mock_post):
        """generate_sql_stream yields individual tokens from the SSE stream."""
        # Simulate Ollama NDJSON streaming response
        tokens = ["SELECT", " *", " FROM", " customers", ";"]
        lines = []
        for i, tok in enumerate(tokens):
            is_last = i == len(tokens) - 1
            lines.append(
                json.dumps({"message": {"content": tok}, "done": is_last}).encode()
            )

        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.raise_for_status = MagicMock()
        mock_resp.iter_lines = MagicMock(return_value=lines)
        mock_post.return_value = mock_resp

        collected = list(
            generate_sql_stream("Show all customers", SAMPLE_SCHEMA, LANG_ENGLISH)
        )

        assert len(collected) == len(tokens)
        assert "".join(collected).strip().upper().startswith("SELECT")

    @patch("backend.app.sql_engine.requests.post")
    def test_stream_payload_uses_stream_true(self, mock_post):
        """generate_sql_stream sends stream=True in the payload."""
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.raise_for_status = MagicMock()
        mock_resp.iter_lines = MagicMock(
            return_value=[json.dumps({"message": {"content": "SELECT 1;"}, "done": True}).encode()]
        )
        mock_post.return_value = mock_resp

        list(generate_sql_stream("q", SAMPLE_SCHEMA, LANG_ENGLISH))

        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs.get("json", {})
        assert payload.get("stream") is True
