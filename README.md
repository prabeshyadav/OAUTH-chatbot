# NexusAI OAuth & RAG Chatbot 🚀

A full-stack, enterprise-grade AI Chatbot application powered by **Google Gemini AI**, **Google OAuth 2.0**, and **Retrieval-Augmented Generation (RAG)**. Built with a **FastAPI** backend, **React 19 + Vite** frontend, **PostgreSQL** for persistence, **ChromaDB** for vector storage, and **Redis + Celery** for asynchronous task execution.

---

## 🌟 Key Features

- 🔐 **Secure Authentication**: 
  - Google OAuth 2.0 single sign-on with automatic JWT access token generation.
  - JWT Bearer token security across protected endpoints.
  - Integration support for Authentik OIDC providers.

- 🤖 **Google Gemini AI Integration**:
  - Leverages Google's latest models (`gemini-2.0-flash` with automatic fallback to `gemini-3-flash-preview`).
  - System prompt customized safety guidelines and structured output processing.

- 📄 **Document Upload & Dual RAG Modes**:
  - **PDF Direct Mode (`pdf`)**: Directly uploads documents to Gemini File API for context-aware conversation across whole documents.
  - **RAG Mode (`rag`)**: Splits documents into chunks using RecursiveCharacterTextSplitter and stores vector embeddings in **ChromaDB** for semantic retrieval.
  - **Auto Mode (`auto`)**: Automatically toggles document context when a file is uploaded.

- ⚡ **Asynchronous Background Processing**:
  - Offloads vector indexing and heavy document ingestion to **Celery workers** backed by **Redis**, ensuring smooth API performance with fallback handling.

- 💬 **Persistent History & User Management**:
  - Chat history and document metadata persisted per user in **PostgreSQL** using **SQLModel**.
  - Endpoint options to view or clear past chat history and manage uploaded PDF files.

- 🎨 **Modern Responsive UI**:
  - Sleek React 19 interface styled with clean CSS, dark themes, and micro-interactions.
  - Markdown rendering with syntax highlighting (`marked`, `highlight.js`) and Lucide React icons.

- 🐳 **Containerized & Production Ready**:
  - Full multi-container setup via `docker-compose` (FastAPI, React, Nginx proxy, Postgres, Redis, Celery).
  - Ready for cloud deployment on **Railway**, **Vercel**, or **Docker** hosts.

---

## 🏗️ Architecture Overview

```
                          ┌──────────────────────────┐
                          │   React 19 + Vite UI     │
                          │    (Nginx / Port 5173)   │
                          └─────────────┬────────────┘
                                        │
                                 HTTP / REST
                                        │
                          ┌─────────────▼────────────┐
                          │   FastAPI Backend Server │
                          │     (Python / Port 8000) │
                          └──────┬──────┬─────┬──────┘
                                 │      │     │
            ┌────────────────────┘      │     └────────────────────┐
            ▼                           ▼                          ▼
 ┌─────────────────────┐     ┌────────────────────┐      ┌────────────────────┐
 │  PostgreSQL Database│     │    Redis Cache     │      │ Google Gemini API  │
 │  (Chat & User DB)   │     │  & Celery Queue    │      │  (AI & File API)   │
 └─────────────────────┘     └──────────┬─────────┘      └────────────────────┘
                                        │
                             ┌──────────▼─────────┐
                             │   Celery Worker    │
                             │   (Ingests RAG)    │
                             └──────────┬─────────┘
                                        │
                             ┌──────────▼─────────┐
                             │     ChromaDB       │
                             │  (Vector Embeddings│
                             └────────────────────┘
```

---

## 📁 Repository Structure

```
OAUTH-chatbot/
├── backend/
│   ├── core/
│   │   ├── auth.py          # JWT authentication helpers & security
│   │   ├── authentik.py     # Authentik OAuth client helpers
│   │   ├── celery_app.py    # Asynchronous background tasks
│   │   ├── chat_crude.py    # Database CRUD logic for chat & files
│   │   ├── database.py      # SQLModel engine & session management
│   │   ├── google_auth.py   # Google OAuth 2.0 login & callback routes
│   │   ├── models.py        # SQLModel table schemas (User, ChatMessage, UserFile)
│   │   └── rag_utils.py     # PDF chunking, ChromaDB vector ingestion & search
│   ├── main.py              # Main FastAPI application & endpoint definitions
│   ├── Dockerfile           # Backend container build configuration
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/                 # React components, API services, and styles
│   ├── package.json         # React & Vite dependencies
│   ├── nginx.conf           # Frontend container Nginx config
│   └── Dockerfile           # Frontend container build configuration
├── nginx/
│   └── nginx.conf           # Root Nginx reverse proxy configuration
├── docker-compose.yml       # Docker Compose multi-service orchestration
├── .env.example             # Environment variable template
├── railway.toml             # Railway deployment config
└── README.md                # Project documentation
```

---

## 🛠️ Prerequisites

- **Docker & Docker Compose** (Recommended for local setup)
- **Python 3.10+** (For manual backend development)
- **Node.js 18+ & npm** (For manual frontend development)
- **Google Gemini API Key** ([Get one here](https://aistudio.google.com/))
- **Google OAuth 2.0 Credentials** ([Google Cloud Console](https://console.cloud.google.com/))

---

## 🚀 Quick Start with Docker Compose

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/prabeshyadav/OAUTH-chatbot.git
   cd OAUTH-chatbot
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```
   *Update `GOOGLE_API_KEY`, `GOOGLE_CLIENT_ID`, and `GOOGLE_CLIENT_SECRET` in `.env`.*

3. **Build and Run Services**:
   ```bash
   docker-compose up --build
   ```

4. **Access the Application**:
   - **Frontend App**: [http://localhost:5173](http://localhost:5173) or [http://localhost:8000](http://localhost:8000)
   - **Backend API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 💻 Manual Local Development Setup

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set environment variables or ensure your `.env` file in the root directory contains valid connection settings for PostgreSQL and Redis, then run:

```bash
uvicorn main:app --reload --port 8000
```

To run the Celery worker for background RAG indexing:
```bash
celery -A core.celery_app.celery_app worker --loglevel=info
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend development server will start on [http://localhost:5173](http://localhost:5173).

---

## 🔑 Environment Variables Reference

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `GOOGLE_API_KEY` | Google Gemini API Key | `AIzaSy...` |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | `xxx.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | `GOCSPX-...` |
| `GOOGLE_REDIRECT_URI` | OAuth Redirect Callback URL | `http://localhost:8000/auth/callback` |
| `SECRET_KEY` | Secret key for signing JWT tokens | `super-secret-key` |
| `DATABASE_URL` | PostgreSQL Connection URI | `postgresql://postgres:postgres@db:5432/chatbot_db` |
| `REDIS_URL` | Redis Connection URI | `redis://redis:6379/0` |
| `FRONTEND_URL` | Target UI URL after OAuth login | `http://localhost:5173` |
| `CORS_ORIGINS` | Allowed origins for CORS requests | `*` |

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/health` | Server health check endpoint | ❌ |
| `GET` | `/auth/login` | Redirect to Google OAuth authorization | ❌ |
| `GET` | `/auth/callback` | Google OAuth callback handler | ❌ |
| `POST` | `/token` | OAuth2 password token login | ❌ |
| `POST` | `/chat` | Send message (`mode`: `auto`, `chat`, `pdf`, `rag`) |  Yes (JWT) |
| `GET` | `/chat/history` | Fetch user chat history |  Yes (JWT) |
| `DELETE` | `/chat/history` | Clear user chat history |  Yes (JWT) |
| `POST` | `/upload-pdf` | Upload PDF for direct chat & vector RAG indexing |  Yes (JWT) |
| `GET` | `/upload-pdf` | Get current active PDF status |  Yes (JWT) |
| `DELETE` | `/upload-pdf` | Delete uploaded PDF metadata |  Yes (JWT) |

---

## ☁️ Deployment

### Deploying to Railway
The project includes `railway.toml`, `railway.json`, and `nixpacks.toml` configurations.
1. Connect your repository on [Railway](https://railway.app/).
2. Attach a PostgreSQL and Redis database service.
3. Configure the environment variables in Railway service settings according to `RAILWAY_DEPLOYMENT.md`.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
