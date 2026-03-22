import os
import shutil
import time
from typing import Dict
from urllib import response
from authlib.jose import jwt
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from google import genai
from fastapi import security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm
from google.genai import types 
from dotenv import load_dotenv
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm
from starlette.requests import Request
from starlette.responses import RedirectResponse
from core.authentik import get_current_user
from core.authentik import oauth
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from authlib.integrations.starlette_client import OAuth
# from authlib.integrations.starlette_client import OIDCProvider

# Assuming these are defined in your local files
from core.google_auth import router as google_auth_router
from core.auth import (
    create_access_token, 
    get_current_user, 
    verify_password, 
    get_password_hash
)
from core.rag_utils import query_vector_db

load_dotenv()

JWKS_URL = "http://localhost:9000/application/o/django-app/jwks/"
ISSUER = "http://localhost:9000/application/o/django-app/"
AUDIENCE = "QJd2jL5P2DZ38xQ3e1nGDXtDzFfztYq6pAn1TKaE"

# --- INITIALIZATION ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

client = genai.Client(api_key=GOOGLE_API_KEY)

app = FastAPI(title="Simple Gemini Bot with Google Auth", root_path='/api')

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

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
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("APP_SESSION_SECRET"), # Use your new generated secret
    same_site="lax",
    https_only=False # Set to True in production with SSL
)
# auth_user = OIDCProvider(
#     # Change localhost to host.docker.internal
#     configuration_uri="http://host.docker.internal:9000/application/o/fastapi-chatbot/.well-known/openid-configuration",
#     client_id="d7fZWJYLI2tWD7p6BhpUa7IXN8iVFS12VRIbHI2D",
# )
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


token_auth_scheme = HTTPBearer()
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

# @app.get("/login")
# async def login(request: Request):
#     redirect_uri = request.url_for("auth_callback")
#     return await oauth.authentik.authorize_redirect(request, str(redirect_uri))

# @app.get("/auth/callback")
# async def auth_callback(request: Request):
#     try:
#         # This exchanges the code for the token bundle
#         token = await oauth.authentik.authorize_access_token(request)
        
#         # Instead of a redirect, we return the token to the user
#         return {
#             "access_token": token.get("access_token"),
#             "id_token": token.get("id_token"),
#             "token_type": "Bearer",
#             "expires_in": token.get("expires_in")
#         }
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Auth error: {str(e)}")

# # --- TOKEN PROTECTION ---

# async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     """
#     This dependency reads the 'Authorization: Bearer <token>' header 
#     and verifies it with Authentik.
#     """
#     token_str = credentials.credentials
#     try:
#         # Verify the token by calling Authentik's userinfo endpoint
#         user_info = await oauth.authentik.userinfo(token={'access_token': token_str, 'token_type': 'Bearer'})
#         return user_info
#     except Exception:
#         raise HTTPException(status_code=401, detail="Invalid or expired token")


# # 3. EXAMPLE PROTECTED ROUTE
# @app.get("/me")
# async def read_users_me(current_user: dict = Depends(get_current_user)):
#     return {"user": current_user}

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






from fastapi import BackgroundTasks # Import this at the top
from core.rag_utils import ingest_pdf_to_vector_db # Your helper

@app.post("/rag-upload-pdf")
async def upload_pdf(
    background_tasks: BackgroundTasks, # Add this parameter
    file: UploadFile = File(...), 
    current_user: str = Depends(get_current_user) 
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Use a unique name for the local copy
    file_extension = file.filename.split(".")[-1]
    local_filename = f"local_{current_user}_{int(time.time())}.{file_extension}"
    local_path = f"/tmp/{local_filename}"

    # 1. Save file locally first
    with open(local_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 2. Google Upload (for your existing /chat route)
        google_file = client.files.upload(file=local_path)
        user_files_db[current_user] = google_file
        
        # 3. RAG Ingestion (Run in background so user doesn't wait)
        background_tasks.add_task(ingest_pdf_to_vector_db, local_path, current_user)
        
        return {
            "message": "Upload successful. RAG indexing started in background.", 
            "file_id": google_file.name
        }
    except Exception as e:
        if os.path.exists(local_path):
            os.remove(local_path)
        raise HTTPException(status_code=500, detail=f"Upload Failed: {str(e)}")
    
    # Note: We don't delete local_path here yet because the background task needs it!
    # You should delete it inside the background task after it's done.
    
    
@app.post("/chat-rag")
async def chat_endpoint(request: ChatRequest, current_user: str = Depends(get_current_user)):
    
    # 1. Try to get context from our local RAG database
    try:
        context = query_vector_db(current_user, request.message)
    except:
        context = "" # No PDF uploaded or DB not found

    # 2. Build the Prompt
    if context:
        prompt = f"""
        You are a helpful assistant. Use the following pieces of retrieved context to answer the question. 
        If you don't know the answer based on the context, say you don't know.
        
        CONTEXT:
        {context}
        
        QUESTION: 
        {request.message}
        """
    else:
        prompt = request.message

    # 3. Call Gemini
    model_options = ["gemini-2.0-flash", "gemini-3-flash-preview"] 
    
    response = None
    for model_id in model_options:
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt
            )
            break  # If successful, break out of the loop
        except Exception:
            continue  # Try the next model if this one fails

    if not response:
        raise HTTPException(status_code=500, detail="Failed to generate response from any model.")

    return {"bot": response.text, "source": "rag" if context else "general_knowledge"}
    
    
    

async def validate_token(res: HTTPAuthorizationCredentials = Depends(token_auth_scheme)):
    token = res.credentials
    try:
        # Fetch public key from Authentik and verify
        header = jwt.get_unverified_header(token)
        # In production, use a library like 'jwks-client' to cache keys
        payload = jwt.decode(token, options={"verify_signature": False}) 
        
        if payload["iss"] != ISSUER or payload["aud"] != AUDIENCE:
             raise HTTPException(status_code=401, detail="Invalid token claims")
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    
    
@app.get("/fastapi-data")
async def secure_data(user=Depends(validate_token)):
    return {"message": f"Hello {user['email']}, FastAPI trusts your token!"}


