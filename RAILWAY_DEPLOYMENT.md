# 🚀 Hybrid Deployment Guide: Vercel Frontend + Railway Backend

Your frontend is deployed at: **`https://oauth-chatbot.vercel.app/`**

Follow these instructions to connect your **Vercel Frontend** to your **Railway Backend & PostgreSQL Database**.

---

## ⚙️ 1. Vercel Configuration (`https://oauth-chatbot.vercel.app/`)

In your **Vercel Dashboard**:
1. Select your project **oauth-chatbot**.
2. Go to **Settings** $\rightarrow$ **Environment Variables**.
3. Add the following variable:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://<your-backend-railway-domain>.up.railway.app`
4. Go to **Deployments** $\rightarrow$ Click the **...** menu on the latest deployment $\rightarrow$ Select **Redeploy** (important so Vite embeds the variable into the build bundle).

---

## 🚂 2. Railway Configuration (FastAPI Backend + PostgreSQL)

In your **Railway Dashboard**:

### A. Add PostgreSQL Database
1. Click **+ New** $\rightarrow$ **Database** $\rightarrow$ **PostgreSQL**.

### B. Deploy Backend Service (`/backend`)
1. Click **+ New** $\rightarrow$ **GitHub Repo** $\rightarrow$ select `OAUTH-chatbot`.
2. In **Settings**:
   - **Root Directory**: `backend`
3. In **Variables**, add:
   - `DATABASE_URL`: `${{Postgres.DATABASE_URL}}`
   - `SECRET_KEY`: Set a secure random string
   - `CORS_ORIGINS`: `https://oauth-chatbot.vercel.app`
   - `FRONTEND_URL`: `https://oauth-chatbot.vercel.app`
   - `GOOGLE_API_KEY`: Your Gemini API Key
   - `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID
   - `GOOGLE_CLIENT_SECRET`: Your Google OAuth Client Secret
   - `GOOGLE_REDIRECT_URI`: `https://<your-backend-railway-domain>.up.railway.app/auth/callback`
4. In **Networking**:
   - Click **Generate Domain** to get your public backend URL (e.g., `https://backend-production-xxxx.up.railway.app`).

---

## 🔑 3. Google Cloud Console Configuration

1. Go to [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials).
2. Edit your OAuth 2.0 Client ID.
3. Under **Authorized JavaScript origins**, add:
   ```
   https://oauth-chatbot.vercel.app
   ```
4. Under **Authorized redirect URIs**, add your Railway backend URL:
   ```
   https://<your-backend-railway-domain>.up.railway.app/auth/callback
   ```
5. Click **Save**.

---

## ⚡ 4. Verification

1. Open `https://oauth-chatbot.vercel.app/`.
2. Try logging in with default credentials `admin` / `password123` or **Sign in with Google OAuth**.
3. Test PDF upload and chatting!
