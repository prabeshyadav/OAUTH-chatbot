import os
from fastapi import APIRouter, Request, HTTPException
from authlib.integrations.starlette_client import OAuth
from core.auth import create_access_token # Import your JWT creator
from dotenv import load_dotenv

load_dotenv()
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['AUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Setup OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@router.get("/login")
async def login_google(request: Request):
    redirect_uri = "http://localhost:8000/auth/callback"  # exactly what you registered in Google
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/callback", name="auth_callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(status_code=400, detail="No user info returned")
            
        email = user_info['email']
        access_token = create_access_token(data={"sub": email})
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        print(f"Detailed Auth Error: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"Authentication failed: {str(e)}"
        )  