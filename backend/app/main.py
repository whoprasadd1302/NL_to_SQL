import io
import csv
import json
import time
import logging
import re
from typing import Any, Dict, List, Optional, Union
from fastapi import FastAPI, HTTPException, Depends, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from .llm import generate_response, stream_response
from .database import engine, Base, get_db, SessionLocal
from .schema_inspector import get_database_schema, format_schema_for_prompt, execute_safe_sql
from . import crud
from .schema_manager import get_target_db_schema, get_schema_context
from .sql_engine import generate_sql, generate_sql_stream, extract_sql
from .sql_validator import validate_sql
from .db_executor import execute_query
from .result_processor import process_results

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mitraai")

app = FastAPI(
    title="MitraAI",
    description="LLM-Based Multilingual Conversational Chatbot & NL-to-SQL System",
    version="0.4.0",
)


@app.on_event("startup")
def startup_db_client():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Successfully connected to database and initialized tables.")
    except Exception as e:
        logger.warning(
            f"Database table initialization notice ({e})."
        )


# ── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Schemas ─────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    target_language: Optional[str] = "Auto-Detect"


class ChatResponse(BaseModel):
    response: str
    session_id: str = "default"
    target_language: Optional[str] = "Auto-Detect"
    sql_result: Optional[Dict[str, Any]] = None


def extract_and_execute_sql(text_response: str) -> Optional[Dict[str, Any]]:
    """
    Extracts the first ```sql ... ``` block from the LLM response text,
    executes it safely, and returns the result dict or None if no query found.
    """
    # Match ```sql ... ``` (possibly with whitespace/newlines)
    pattern = r"```sql\s*([\s\S]+?)\s*```"
    match = re.search(pattern, text_response, re.IGNORECASE)
    if not match:
        return None

    sql_query = match.group(1).strip()
    if not sql_query:
        return None

    logger.info(f"Auto-executing extracted SQL: {sql_query[:120]}...")
    result = execute_safe_sql(sql_query)
    return result


class MessageSchema(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str

    class Config:
        from_attributes = True


class SessionCreateSchema(BaseModel):
    title: Optional[str] = "New Chat"


class SessionUpdateSchema(BaseModel):
    title: str


class SessionSchema(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int

    class Config:
        from_attributes = True


class SQLRequest(BaseModel):
    query: str
    language: Optional[str] = "auto"
    session_id: Optional[str] = "default"
    db_path: Optional[str] = None


class ExportRequest(BaseModel):
    query: Optional[str] = None
    sql: Optional[str] = None
    db_path: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None


def resolve_language_info(lang: Optional[str]) -> tuple[str, str]:
    """Maps language input code/string to standard tuple (lang_code, lang_name)."""
    if not lang or lang.lower() in ("auto", "auto-detect", "en", "english"):
        return "en", "English"
    lower = lang.lower()
    if "hi" in lower or "हिंदी" in lang:
        return "hi", "Hindi"
    if "mr" in lower or "मराठी" in lang:
        return "mr", "Marathi"
    if "hinglish" in lower:
        return "hinglish", "Hinglish"
    return "en", "English"


# ── Root & Health Endpoints ──────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "Welcome to MitraAI",
        "status": "Backend is running",
        "model": "qwen3:8b",
        "provider": "Ollama",
        "supported_languages": ["Auto-Detect", "English", "Hindi (हिंदी)", "Marathi (मराठी)", "Hinglish"],
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/health/db")
def db_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection check: {str(e)}"
        )


# ── Session Management Endpoints ─────────────────────────────────────
@app.get("/sessions", response_model=List[SessionSchema])
def list_sessions(db: Session = Depends(get_db)):
    try:
        sessions = crud.get_all_sessions(db)
        return [
            SessionSchema(
                id=s.id,
                title=s.title or "New Chat",
                created_at=s.created_at.isoformat() if s.created_at else "",
                updated_at=s.updated_at.isoformat() if s.updated_at else "",
                message_count=len(s.messages) if s.messages else 0,
            )
            for s in sessions
        ]
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        return [
            SessionSchema(
                id="default",
                title="New Chat",
                created_at="",
                updated_at="",
                message_count=0,
            )
        ]


@app.post("/sessions", response_model=SessionSchema)
def create_session(payload: SessionCreateSchema = SessionCreateSchema(), db: Session = Depends(get_db)):
    try:
        session = crud.create_session(db, title=payload.title or "New Chat")
        return SessionSchema(
            id=session.id,
            title=session.title,
            created_at=session.created_at.isoformat() if session.created_at else "",
            updated_at=session.updated_at.isoformat() if session.updated_at else "",
            message_count=0,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@app.patch("/sessions/{session_id}", response_model=SessionSchema)
def update_session(session_id: str, payload: SessionUpdateSchema, db: Session = Depends(get_db)):
    session = crud.update_session_title(db, session_id, payload.title)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionSchema(
        id=session.id,
        title=session.title,
        created_at=session.created_at.isoformat() if session.created_at else "",
        updated_at=session.updated_at.isoformat() if session.updated_at else "",
        message_count=len(session.messages) if session.messages else 0,
    )


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    success = crud.delete_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success", "message": f"Session {session_id} deleted"}


# ── Message History Endpoints ─────────────────────────────────────────
@app.get("/history", response_model=List[MessageSchema])
def get_history(session_id: str = Query("default"), db: Session = Depends(get_db)):
    try:
        messages = crud.get_messages(db, session_id=session_id)
        return [
            MessageSchema(
                id=m.id,
                role=m.role,
                content=m.content,
                timestamp=m.timestamp.isoformat() if m.timestamp else "",
            )
            for m in messages
        ]
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return []


@app.delete("/history")
def clear_history(session_id: str = Query("default"), db: Session = Depends(get_db)):
    try:
        crud.clear_messages(db, session_id=session_id)
        return {"status": "success", "message": "History cleared"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear history: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    session_id = request.session_id or "default"
    target_language = request.target_language or "Auto-Detect"

    prior_messages = []
    try:
        raw_msgs = crud.get_messages(db, session_id=session_id)
        prior_messages = [{"role": m.role, "content": m.content} for m in raw_msgs]
    except Exception as e:
        logger.warning(f"Could not load prior history: {e}")

    try:
        crud.add_message(db, session_id=session_id, role="user", content=request.message.strip())
    except Exception as e:
        logger.warning(f"Could not save user message to DB: {e}")

    # Introspect database schema for NL-to-SQL context
    schema_context = None
    try:
<<<<<<< HEAD
=======
        current_schema = get_database_schema()
        if current_schema:
            schema_context = format_schema_for_prompt(current_schema)
    except Exception as e:
        logger.warning(f"Could not introspect database schema: {e}")

    try:
        # 2. Generate LLM response with conversation context, target language, and DB schema
>>>>>>> 9b3a9e4 (feat: Add PostgreSQL dataset integration, automatic NL-to-SQL execution, and markdown/table rendering in UI)
        response = generate_response(
            request.message,
            history=prior_messages,
            target_language=target_language,
            schema_context=schema_context
        )

<<<<<<< HEAD
=======
        # 3. Auto-execute any SQL query found in the LLM response
        sql_result = None
        try:
            sql_result = extract_and_execute_sql(response)
        except Exception as e:
            logger.warning(f"SQL auto-execution failed: {e}")

        # 4. Save assistant message to DB
>>>>>>> 9b3a9e4 (feat: Add PostgreSQL dataset integration, automatic NL-to-SQL execution, and markdown/table rendering in UI)
        try:
            crud.add_message(db, session_id=session_id, role="assistant", content=response)
        except Exception as e:
            logger.warning(f"Could not save assistant message to DB: {e}")

        return ChatResponse(
            response=response,
            session_id=session_id,
            target_language=target_language,
            sql_result=sql_result,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM error: {str(e)}"
        )


@app.post("/chat/stream")
def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    """Server-Sent Events endpoint that streams tokens in selected target language."""

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    session_id = request.session_id or "default"
    target_language = request.target_language or "Auto-Detect"

<<<<<<< HEAD
=======
    # Introspect database schema for NL-to-SQL context
    schema_context = None
    try:
        current_schema = get_database_schema()
        if current_schema:
            schema_context = format_schema_for_prompt(current_schema)
    except Exception as e:
        logger.warning(f"Could not introspect database schema: {e}")

    # Fetch prior history for context memory
>>>>>>> 9b3a9e4 (feat: Add PostgreSQL dataset integration, automatic NL-to-SQL execution, and markdown/table rendering in UI)
    prior_messages = []
    try:
        raw_msgs = crud.get_messages(db, session_id=session_id)
        prior_messages = [{"role": m.role, "content": m.content} for m in raw_msgs]
    except Exception as e:
        logger.warning(f"Could not load prior history: {e}")

    try:
        crud.add_message(db, session_id=session_id, role="user", content=request.message.strip())
    except Exception as e:
        logger.warning(f"Could not save user message to DB: {e}")

    def event_generator():
        accumulated_text = ""
        try:
            for token in stream_response(
                request.message,
                history=prior_messages,
                target_language=target_language,
                schema_context=schema_context
            ):
                accumulated_text += token
                payload = json.dumps({"token": token})
                yield f"data: {payload}\n\n"

            if accumulated_text.strip():
                try:
                    with SessionLocal() as db_session:
                        crud.add_message(db_session, session_id=session_id, role="assistant", content=accumulated_text)
                except Exception as save_err:
                    logger.warning(f"Failed to save streamed assistant message to DB: {save_err}")

<<<<<<< HEAD
=======
            # Auto-execute any SQL found in the full response
            sql_result = None
            try:
                sql_result = extract_and_execute_sql(accumulated_text)
            except Exception as sql_err:
                logger.warning(f"Streaming SQL auto-execution failed: {sql_err}")

            if sql_result is not None:
                yield f"data: {json.dumps({'sql_result': sql_result})}\n\n"

            # Signal stream end
>>>>>>> 9b3a9e4 (feat: Add PostgreSQL dataset integration, automatic NL-to-SQL execution, and markdown/table rendering in UI)
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


<<<<<<< HEAD
# ── NL-to-SQL Endpoints ───────────────────────────────────────────────

@app.get("/sql/schema")
def get_db_schema(db_path: Optional[str] = Query(None)):
    """Returns target DB schema introspected via SQLAlchemy."""
    try:
        schema = get_target_db_schema(db_path)
        schema_context = get_schema_context("", db_path)
        return {
            "tables": schema.get("tables", []),
            "columns": schema.get("columns", {}),
            "foreign_keys": schema.get("foreign_keys", []),
            "schema_context": schema_context,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch schema: {str(e)}")


@app.post("/sql/stream")
def stream_sql_query(request: SQLRequest, db: Session = Depends(get_db)):
    """Server-Sent Events endpoint for streaming SQL generation."""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    try:
        schema_context = get_schema_context(request.query, request.db_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load schema context: {str(e)}")

    history = []
    if request.session_id:
        try:
            raw_msgs = crud.get_messages(db, session_id=request.session_id)
            history = [{"role": m.role, "content": m.content} for m in raw_msgs]
        except Exception as e:
            logger.warning(f"Could not load history for stream: {e}")

    def event_generator():
        accumulated_sql = ""
        try:
            for token in generate_sql_stream(
                query=request.query,
                schema=schema_context,
                language=request.language,
                history=history,
            ):
                accumulated_sql += token
                payload = json.dumps({"token": token})
                yield f"data: {payload}\n\n"

            clean_sql = extract_sql(accumulated_sql)
            done_payload = json.dumps({"done": True, "sql": clean_sql})
            yield f"data: {done_payload}\n\n"
        except Exception as e:
            err_payload = json.dumps({"error": str(e)})
            yield f"data: {err_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/sql/execute")
def execute_sql_query(request: SQLRequest, db: Session = Depends(get_db)):
    """
    Complete NL-to-SQL endpoint:
    Generates SQL, validates safety, executes against target DB, and returns visual payload.
    """
    start_time = time.time()

    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    lang_code, lang_name = resolve_language_info(request.language)

    # 1. Fetch DB schema
    try:
        schema_context = get_schema_context(request.query, request.db_path)
        target_schema = get_target_db_schema(request.db_path)
    except Exception as e:
        logger.error(f"Error fetching schema: {e}")
        return {
            "success": False,
            "language": lang_code,
            "language_name": lang_name,
            "sql": "",
            "error": f"Failed to inspect database schema: {str(e)}",
            "results": [],
            "summary": "Database schema error.",
            "chart_type": None,
            "chart_data": {},
            "count": 0,
            "execution_time": round(time.time() - start_time, 4),
        }

    # 2. Fetch history if session_id provided
    history = []
    if request.session_id:
        try:
            raw_msgs = crud.get_messages(db, session_id=request.session_id)
            history = [{"role": m.role, "content": m.content} for m in raw_msgs]
        except Exception as e:
            logger.warning(f"Could not load history for SQL generation: {e}")

    # 3. Generate SQL from query
    try:
        generated_sql = generate_sql(
            query=request.query,
            schema=schema_context,
            language=request.language,
            history=history,
        )
    except Exception as e:
        logger.error(f"SQL generation failed: {e}")
        elapsed = round(time.time() - start_time, 4)
        return {
            "success": False,
            "language": lang_code,
            "language_name": lang_name,
            "sql": "",
            "error": f"SQL generation failed: {str(e)}",
            "results": [],
            "summary": f"Could not generate SQL for query: {request.query}",
            "chart_type": None,
            "chart_data": {},
            "count": 0,
            "execution_time": elapsed,
        }

    # 4. Validate SQL statement
    is_valid, val_msg = validate_sql(generated_sql, schema=target_schema)
    if not is_valid:
        elapsed = round(time.time() - start_time, 4)
        return {
            "success": False,
            "language": lang_code,
            "language_name": lang_name,
            "sql": generated_sql,
            "error": f"SQL validation failed: {val_msg}",
            "results": [],
            "summary": f"Generated SQL was rejected due to safety rules: {val_msg}",
            "chart_type": None,
            "chart_data": {},
            "count": 0,
            "execution_time": elapsed,
        }

    # 5. Execute SQL query against target DB
    results, db_err = execute_query(generated_sql, db_path=request.db_path)
    if db_err:
        elapsed = round(time.time() - start_time, 4)
        return {
            "success": False,
            "language": lang_code,
            "language_name": lang_name,
            "sql": generated_sql,
            "error": db_err,
            "results": [],
            "summary": f"Database execution error: {db_err}",
            "chart_type": None,
            "chart_data": {},
            "count": 0,
            "execution_time": elapsed,
        }

    # 6. Process results for summary & visualization
    processed = process_results(results, query=request.query)
    elapsed = round(time.time() - start_time, 4)

    # Save to history if session_id active
    if request.session_id:
        try:
            crud.add_message(db, session_id=request.session_id, role="user", content=request.query)
            crud.add_message(db, session_id=request.session_id, role="assistant", content=f"SQL: {generated_sql}\nResult: {processed['summary']}")
        except Exception as e:
            logger.warning(f"Failed to record SQL query in message history: {e}")

    return {
        "success": True,
        "language": lang_code,
        "language_name": lang_name,
        "sql": generated_sql,
        "results": processed.get("data", []),
        "summary": processed.get("summary", ""),
        "chart_type": processed.get("chart_type"),
        "chart_data": processed.get("chart_data", {}),
        "count": processed.get("row_count", len(results)),
        "execution_time": elapsed,
    }


@app.post("/sql/export")
def export_sql_results(request: ExportRequest):
    """
    Exports query results as a downloadable CSV file.
    Accepts either raw data list or executes provided SQL/query.
    """
    data = request.data
    if data is None and (request.sql or request.query):
        sql_to_run = request.sql
        if not sql_to_run and request.query:
            schema_context = get_schema_context(request.query, request.db_path)
            sql_to_run = generate_sql(request.query, schema_context)

        if sql_to_run:
            results, err = execute_query(sql_to_run, db_path=request.db_path)
            if err:
                raise HTTPException(status_code=400, detail=f"Error executing SQL for export: {err}")
            data = results
        else:
            data = []

    if data is None:
        data = []

    output = io.StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)
    else:
        output.write("No data available\n")

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=query_results.csv"
        }
    )
=======
# ── Database & NL-to-SQL Endpoints ─────────────────────────────────────

class SqlExecuteRequest(BaseModel):
    query: str
    max_rows: Optional[int] = 100


@app.get("/api/database/status")
def get_db_status():
    """Returns the current database engine type, connection status, and detected tables."""
    try:
        url = str(engine.url)
        # Mask password if present in url
        safe_url = url.split("@")[-1] if "@" in url else url
        is_postgres = "postgresql" in url

        schema = get_database_schema()
        table_count = len(schema.keys())

        return {
            "status": "connected",
            "database_type": "PostgreSQL" if is_postgres else "SQLite",
            "connection": safe_url,
            "table_count": table_count,
            "tables": list(schema.keys()),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@app.get("/api/database/schema")
def get_schema_endpoint():
    """Returns detailed schema information (tables, columns, types, keys) of the connected database."""
    schema = get_database_schema()
    formatted = format_schema_for_prompt(schema)
    return {
        "schema": schema,
        "formatted_ddl": formatted,
    }


@app.post("/api/sql/execute")
def execute_sql_endpoint(req: SqlExecuteRequest):
    """Safely executes read-only SQL queries on the connected database."""
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    result = execute_safe_sql(req.query, max_rows=req.max_rows or 100)
    return result
>>>>>>> 9b3a9e4 (feat: Add PostgreSQL dataset integration, automatic NL-to-SQL execution, and markdown/table rendering in UI)
