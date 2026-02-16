import os
import shutil
import time
from typing import Dict
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types 
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordRequestForm

# Assuming these are defined in your local files
from core.google_auth import router as google_auth_router
from core.auth import (
    create_access_token, 
    get_current_user, 
    verify_password, 
    get_password_hash
)

load_dotenv()

# --- INITIALIZATION ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

client = genai.Client(api_key=GOOGLE_API_KEY)

app = FastAPI(title="Simple Gemini Bot with Google Auth", root_path='/api')

# Load System Prompt
try:
    with open("core/system_prompt.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    SYSTEM_PROMPT = "You are a helpful assistant."

# --- MIDDLEWARE ---
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SECRET_KEY", "fallback-secret-key"),
    same_site="lax",
    https_only=False
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(google_auth_router)

# --- DATABASES (Mock) ---
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("password123"),
    }
}

# Stores Google File objects mapped to usernames: {"username": file_object}
user_files_db: Dict[str, any] = {}

class ChatRequest(BaseModel):
    message: str

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
    file: UploadFile = File(...), 
    current_user: str = Depends(get_current_user) 
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    temp_path = f"temp_{current_user}_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Upload to Google Gemini API
        google_file = client.files.upload(file=temp_path)
        # Store the reference in our "database" for this specific user
        user_files_db[current_user] = google_file
        
        return {
            "message": "Upload successful", 
            "file_id": google_file.name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Upload Failed: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, current_user: str = Depends(get_current_user)):
    # Fallback list of models
    # for model_id in model_options:
    #     try:
            
    model_options = ["gemini-2.0-flash", "gemini-3-flash-preview"]  

    safety_config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.7, # Use temperature to control creativity instead
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

    # Check if this user has a PDF uploaded
    user_pdf = user_files_db.get(current_user)

    if user_pdf:
        contents = [
            user_pdf,
            f"Context: Answer strictly using the PDF. Question: {request.message}"
        ]
    else:
        contents = request.message

    for model_id in model_options:
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=contents,
                config=safety_config
            )

            if not response or not response.text:
                return {"bot": "I cannot answer this due to safety policies."}

            return {
                "user": request.message,
                "bot": response.text,
                "mode": "pdf" if user_pdf else "chat",
                "authorized_as": current_user
            }

        except Exception as e:
            # Check for rate limits or model unavailability
            if "429" in str(e) or "404" in str(e):
                continue
            raise HTTPException(status_code=500, detail=f"Model Error: {str(e)}")

    raise HTTPException(status_code=429, detail="All models are currently busy.")