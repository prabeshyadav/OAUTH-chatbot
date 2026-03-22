from sqlmodel import Session, select
from core.models import ChatMessage, UserFile

def get_chat_history(session: Session, username: str, limit: int = 20) -> list:
    messages = session.exec(
        select(ChatMessage)
        .where(ChatMessage.username == username)
        .order_by(ChatMessage.created_at)
        .limit(limit)
    ).all()
    return [{"role": m.role, "parts": [m.content]} for m in messages]

def save_message(session: Session, username: str, role: str, content: str):
    msg = ChatMessage(username=username, role=role, content=content)
    session.add(msg)
    session.commit()

def clear_history(session: Session, username: str):
    messages = session.exec(
        select(ChatMessage).where(ChatMessage.username == username)
    ).all()
    for m in messages:
        session.delete(m)
    session.commit()

def save_user_file(session: Session, username: str, google_file_id: str, filename: str):
    existing = session.exec(
        select(UserFile).where(UserFile.username == username)
    ).first()
    if existing:
        existing.google_file_id = google_file_id
        existing.original_filename = filename
    else:
        session.add(UserFile(username=username, google_file_id=google_file_id, original_filename=filename))
    session.commit()

def get_user_file(session: Session, username: str) -> UserFile | None:
    return session.exec(
        select(UserFile).where(UserFile.username == username)
    ).first()