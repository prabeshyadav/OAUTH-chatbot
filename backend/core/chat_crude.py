from sqlmodel import Session, select
from core.models import ChatMessage, UserFile
from google.genai import types
from core.redis_cache import cache_get, cache_set, cache_delete

def get_chat_history(session: Session, username: str, limit: int = 20) -> list:
    cache_key = f"chat_history:{username}:{limit}"
    cached_data = cache_get(cache_key)
    if cached_data:
        return [
            types.Content(
                role=item["role"],
                parts=[types.Part(text=item["text"])]
            )
            for item in cached_data
        ]

    messages = session.exec(
        select(ChatMessage)
        .where(ChatMessage.username == username)
        .order_by(ChatMessage.created_at)
        .limit(limit)
    ).all()
    
    serialized = [{"role": m.role, "text": m.content} for m in messages]
    cache_set(cache_key, serialized, ttl=300)

    return [
        types.Content(
            role=m.role,
            parts=[types.Part(text=m.content)]
        )
        for m in messages
    ]

def save_message(session: Session, username: str, role: str, content: str):
    msg = ChatMessage(username=username, role=role, content=content)
    session.add(msg)
    session.commit()
    cache_delete(f"chat_history:{username}:20")

def clear_history(session: Session, username: str):
    messages = session.exec(
        select(ChatMessage).where(ChatMessage.username == username)
    ).all()
    for m in messages:
        session.delete(m)
    session.commit()
    cache_delete(f"chat_history:{username}:20")

def save_user_file(session: Session, username: str, google_file_id: str, filename: str):
    existing = session.exec(
        select(UserFile).where(UserFile.username == username)
    ).first()
    if existing:
        existing.google_file_id = google_file_id
        existing.original_filename = filename
        session.add(existing)
    else:
        session.add(UserFile(username=username, google_file_id=google_file_id, original_filename=filename))
    session.commit()
    cache_delete(f"user_file:{username}")

def get_user_file(session: Session, username: str) -> UserFile | None:
    cache_key = f"user_file:{username}"
    cached = cache_get(cache_key)
    if cached:
        file_obj = UserFile(
            username=cached["username"],
            google_file_id=cached["google_file_id"],
            original_filename=cached["original_filename"]
        )
        return file_obj

    file_obj = session.exec(
        select(UserFile).where(UserFile.username == username)
    ).first()
    if file_obj:
        cache_set(cache_key, {
            "username": file_obj.username,
            "google_file_id": file_obj.google_file_id,
            "original_filename": file_obj.original_filename
        }, ttl=600)
    return file_obj