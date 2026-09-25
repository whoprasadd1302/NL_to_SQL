import json
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from .llm import generate_response, stream_response
from .database import engine, Base, get_db, SessionLocal
from . import crud

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mitraai")

app = FastAPI(
    title="MitraAI",
    description="LLM-Based Multilingual Conversational Chatbot with Language Selector & History",
    version="0.3.5",
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


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    target_language: Optional[str] = "Auto-Detect"


class ChatResponse(BaseModel):
    response: str
    session_id: str = "default"
    target_language: Optional[str] = "Auto-Detect"


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

    # Fetch prior history for context memory before saving current msg
    prior_messages = []
    try:
        raw_msgs = crud.get_messages(db, session_id=session_id)
        prior_messages = [{"role": m.role, "content": m.content} for m in raw_msgs]
    except Exception as e:
        logger.warning(f"Could not load prior history: {e}")

    # 1. Save user message to DB
    try:
        crud.add_message(db, session_id=session_id, role="user", content=request.message.strip())
    except Exception as e:
        logger.warning(f"Could not save user message to DB: {e}")

    try:
        # 2. Generate LLM response with conversation context and target language
        response = generate_response(
            request.message,
            history=prior_messages,
            target_language=target_language
        )

        # 3. Save assistant message to DB
        try:
            crud.add_message(db, session_id=session_id, role="assistant", content=response)
        except Exception as e:
            logger.warning(f"Could not save assistant message to DB: {e}")

        return ChatResponse(
            response=response,
            session_id=session_id,
            target_language=target_language,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM error: {str(e)}"
        )


# ── Streaming endpoint with Memory Context & Language Control ─────────
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

    # Fetch prior history for context memory
    prior_messages = []
    try:
        raw_msgs = crud.get_messages(db, session_id=session_id)
        prior_messages = [{"role": m.role, "content": m.content} for m in raw_msgs]
    except Exception as e:
        logger.warning(f"Could not load prior history: {e}")

    # Save user message to DB
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
                target_language=target_language
            ):
                accumulated_text += token
                payload = json.dumps({"token": token})
                yield f"data: {payload}\n\n"

            # Save full assistant message to DB when stream completes
            if accumulated_text.strip():
                try:
                    with SessionLocal() as db_session:
                        crud.add_message(db_session, session_id=session_id, role="assistant", content=accumulated_text)
                except Exception as save_err:
                    logger.warning(f"Failed to save streamed assistant message to DB: {save_err}")

            # Signal stream end
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