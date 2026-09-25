from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import ChatSession, ChatMessage


def create_session(db: Session, title: str = "New Chat", session_id: Optional[str] = None) -> ChatSession:
    kwargs = {"title": title}
    if session_id:
        kwargs["id"] = session_id
    session = ChatSession(**kwargs)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_or_create_session(db: Session, session_id: str = "default") -> ChatSession:
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        session = ChatSession(id=session_id, title="New Chat")
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def get_all_sessions(db: Session) -> List[ChatSession]:
    sessions = (
        db.query(ChatSession)
        .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
        .all()
    )
    if not sessions:
        default_session = create_session(db, title="New Chat", session_id="default")
        return [default_session]
    return sessions


def get_session(db: Session, session_id: str) -> Optional[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def update_session_title(db: Session, session_id: str, title: str) -> Optional[ChatSession]:
    session = get_session(db, session_id)
    if session:
        session.title = title
        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
    return session


def delete_session(db: Session, session_id: str) -> bool:
    session = get_session(db, session_id)
    if session:
        db.delete(session)
        db.commit()
        return True
    return False


def touch_session(db: Session, session_id: str):
    session = get_session(db, session_id)
    if session:
        session.updated_at = datetime.utcnow()
        db.commit()


def auto_title_session_if_needed(db: Session, session_id: str, first_user_message: str):
    session = get_session(db, session_id)
    if session and (session.title == "New Chat" or not session.title):
        clean_text = first_user_message.strip().replace("\n", " ")
        if len(clean_text) > 35:
            clean_text = clean_text[:35] + "..."
        session.title = clean_text or "New Chat"
        session.updated_at = datetime.utcnow()
        db.commit()


def get_messages(db: Session, session_id: str = "default"):
    get_or_create_session(db, session_id)
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )


def add_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    msg_id: Optional[str] = None,
    sql_result: Optional[str] = None
) -> ChatMessage:
    session = get_or_create_session(db, session_id)
    msg_kwargs = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "sql_result": sql_result,
    }
    if msg_id:
        msg_kwargs["id"] = msg_id
    message = ChatMessage(**msg_kwargs)
    db.add(message)

    # Touch session timestamp
    session.updated_at = datetime.utcnow()

    # Auto title if first user message
    if role == "user":
        msg_count = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()
        if msg_count == 0:
            auto_title_session_if_needed(db, session_id, content)

    db.commit()
    db.refresh(message)
    return message


def clear_messages(db: Session, session_id: str = "default"):
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.commit()
