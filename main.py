import os
import shutil
import time
from typing import Optional
from authlib.jose import jwt
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from sqlmodel import Session
from core.database import get_session
from core.database import create_db_and_tables
from core.chat_crude import get_chat_history, save_message, clear_history, save_user_file, get_user_file
from core.google_auth import router as google_auth_router
from core.auth import (
    create_access_token,
    get_current_user,
    verify_password,
    get_password_hash
)
from core.database import create_db_and_tables, get_session

from core.rag_utils import query_vector_db, ingest_pdf_to_vector_db

load_dotenv()

JWKS_URL = "http://localhost:9000/application/o/django-app/jwks/"
ISSUER = "http://localhost:9000/application/o/django-app/"
AUDIENCE = "QJd2jL5P2DZ38xQ3e1nGDXtDzFfztYq6pAn1TKaE"

# --- INITIALIZATION ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

client = genai.Client(api_key=GOOGLE_API_KEY)

app = FastAPI(title="Gemini Chatbot", root_path='/api')

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Load System Prompt
try:
    with open("core/system_prompt.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    SYSTEM_PROMPT = "You are a helpful assistant."

# --- MIDDLEWARE (only once each) ---
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "fallback-secret-key"),
    same_site="lax",
    https_only=False
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(google_auth_router)

# --- STARTUP ---
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- MOCK USER DB (replace with real DB later) ---
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("password123"),
    }
}

# --- MODELS ---
class ChatRequest(BaseModel):
    message: str
    mode: Optional[str] = "auto"  # "auto", "chat", "pdf", "rag"

# --- AUTH ---
token_auth_scheme = HTTPBearer()
MODEL_OPTIONS = ["gemini-2.0-flash", "gemini-3-flash-preview"]

# --- HELPERS ---
def get_safety_config():
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.7,
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            ),
        ]
    )

def call_gemini(contents):
    for model_id in MODEL_OPTIONS:
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=contents,
                config=get_safety_config()
            )
            if response and response.text:
                return response.text, model_id
        except Exception as e:
            if "429" in str(e) or "404" in str(e):
                continue
            raise HTTPException(status_code=500, detail=f"Model error: {str(e)}")
    raise HTTPException(status_code=429, detail="All models are currently busy.")

# --- ROUTES ---

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/upload-pdf")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    local_path = f"/tmp/{current_user}_{int(time.time())}.pdf"

    with open(local_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Upload to Gemini for direct PDF chat
        google_file = client.files.upload(file=local_path)

        # Save file reference to PostgreSQL
        save_user_file(session, current_user, google_file.name, file.filename)

        # Index into RAG vector DB in background
        background_tasks.add_task(ingest_pdf_to_vector_db, local_path, current_user)

        return {
            "message": "PDF uploaded. RAG indexing started in background.",
            "file_id": google_file.name,
            "tip": "Use mode='pdf' for direct PDF chat, mode='rag' for vector search"
        }
    except Exception as e:
        if os.path.exists(local_path):
            os.remove(local_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.delete("/upload-pdf")
async def delete_pdf(
    current_user: str = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    user_file = get_user_file(session, current_user)
    if not user_file:
        raise HTTPException(status_code=404, detail="No PDF found for this user")
    from core.models import UserFile
    from sqlmodel import select
    from core.models import UserFile
    db_file = session.exec(
        select(UserFile).where(UserFile.username == current_user)
    ).first()
    if db_file:
        session.delete(db_file)
        session.commit()
    return {"message": "PDF removed successfully"}

@app.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    current_user: str = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    history = get_chat_history(session, current_user)
    user_file = get_user_file(session, current_user)
    mode = request.mode

    if mode == "auto":
        mode = "pdf" if user_file else "chat"

    # --- PDF MODE ---
    if mode == "pdf":
        if not user_file:
            raise HTTPException(status_code=400, detail="No PDF uploaded.")
        google_file = client.files.get(name=user_file.google_file_id)
        # PDF mode: file + history + new question
        contents = [google_file] + history + [
            types.Content(
                role="user",
                parts=[types.Part(text=f"Answer using the PDF only. Question: {request.message}")]
            )
        ]
        bot_reply, model_used = call_gemini(contents)

    # --- RAG MODE ---
    elif mode == "rag":
        try:
            context = query_vector_db(current_user, request.message)
        except Exception:
            context = ""

        prompt = f"""Use the context below to answer. If not in context, say you don't know.

CONTEXT:
{context}

QUESTION: {request.message}""" if context else request.message

        contents = history + [
            types.Content(role="user", parts=[types.Part(text=prompt)])
        ]
        bot_reply, model_used = call_gemini(contents)

    # --- CHAT MODE ---
    else:
        contents = history + [
            types.Content(role="user", parts=[types.Part(text=request.message)])
        ]
        bot_reply, model_used = call_gemini(contents)

    # Save to PostgreSQL
    save_message(session, current_user, "user", request.message)
    save_message(session, current_user, "model", bot_reply)

    return {
        "user": request.message,
        "bot": bot_reply,
        "mode": mode,
        "model": model_used,
        "authorized_as": current_user
    }

@app.get("/chat/history")
async def fetch_history(
    current_user: str = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    history = get_chat_history(session, current_user)
    return {"username": current_user, "history": history}


@app.delete("/chat/history")
async def delete_history(
    current_user: str = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    clear_history(session, current_user)
    return {"message": "Chat history cleared"}


# --- AUTHENTIK TOKEN VALIDATION (optional route) ---
async def validate_token(res: HTTPAuthorizationCredentials = Depends(token_auth_scheme)):
    token = res.credentials
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        if payload["iss"] != ISSUER or payload["aud"] != AUDIENCE:
            raise HTTPException(status_code=401, detail="Invalid token claims")
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/fastapi-data")
async def secure_data(user=Depends(validate_token)):
    return {"message": f"Hello {user['email']}, FastAPI trusts your token!"}