import os
from fastapi import Request, HTTPException # Correct import for FastAPI
from dotenv import load_dotenv
from authlib.integrations.starlette_client import OAuth

load_dotenv()

# Initialize OAuth registry
oauth = OAuth()

# Register Authentik
oauth.register(
    name='authentik',
    client_id=os.getenv("AUTHENTIK_CLIENT_ID"),
    client_secret=os.getenv("AUTHENTIK_CLIENT_SECRET"),
    server_metadata_url=os.getenv("AUTHENTIK_METADATA_URL"),
    client_kwargs={'scope': 'openid profile email'},
)

async def get_current_user(request: Request):
    user = request.session.get('user')
    if not user:
        # Using the FastAPI HTTPException ensures the client gets a 401 error
        raise HTTPException(status_code=401, detail="Not authenticated via Authentik")
    return user