# 🤖 LangGraph RAG Agent

An agentic Retrieval-Augmented Generation (RAG) system built with **FastAPI** and **LangGraph**, featuring streaming responses, a **PostgreSQL + pgvector** vector store, and a modern **Streamlit** UI. The system supports user authentication, threaded conversations with persistent memory via LangGraph Postgres checkpointers, and tool-augmented reasoning (document retrieval + web search).

## 🚀 Features

- **Agentic RAG with LangGraph**: ReAct-style agent with tools for document retrieval and web search
- **Streaming responses end-to-end**: Real-time token streaming from backend to the Streamlit UI
- **Threaded conversations**: Per-user threads with persistent histories stored via Postgres checkpointers
- **PostgreSQL + pgvector**: Vector storage and semantic retrieval over user-uploaded documents
- **Authentication and JWT**: Signup, login, refresh; per-user isolation for threads and docs
- **Document ingestion**: PDF, DOCX, and TXT support with chunking and async indexing
- **Tooling**: Built-in `retrieve_user_documents` and Tavily web search integration
- **Async-first backend**: FastAPI + SQLAlchemy 2.0 async, production-ready logging and healthchecks

## 💻 Tech Stack

- **Backend**: FastAPI, LangGraph, LangChain, SQLAlchemy, Pydantic v2
- **Vector Store**: PostgreSQL + pgvector (via `langchain-postgres`)
- **Checkpointer**: LangGraph Postgres Checkpointer (async)
- **Frontend**: Streamlit
- **LLM/Embeddings**: OpenAI-compatible models (configurable base URLs)

## 📋 Prerequisites

- Python 3.12+
- Docker and Docker Compose (recommended for Postgres + full stack)

## 📦 Quick Start (Docker Compose)

1. Copy environment template and edit values:
   ```bash
   cp env.example .env
   ```
2. Start the full stack:
   ```bash
   docker compose up --build
   ```

Services:
- Backend API: `http://localhost:8000/api/v1`
- API Docs: `http://localhost:8000/api/v1/docs`
- Frontend UI: `http://localhost:8501`

Notes:
- The `pgvector/pgvector:pg16` image includes the `vector` extension. If you use your own Postgres, ensure `CREATE EXTENSION IF NOT EXISTS vector;` is enabled.

## 🧰 Local Development

### 1) Backend (FastAPI)

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate     # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

Ensure a Postgres instance is running with pgvector. Example (Docker):
```bash
docker run --name langgraph_postgres -p 5432:5432 \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=test -e POSTGRES_DB=langgraph_db \
  -d pgvector/pgvector:pg16
```

Run the API:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --reload-dir ./app
```

### 2) Frontend (Streamlit)

```bash
cd frontend
python -m venv .venv
.venv/Scripts/activate     # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
streamlit run gui/main.py
```

## 🔧 Environment Variables

Create a project-root `.env` (both backend and frontend read from it). Key settings:

Core LLM settings:
- `OPENAI_API_KEY`
- `MODEL_PROVIDER` (e.g., `openai`)
- `MODEL_NAMES` (JSON list, e.g., `["gpt-4o", "gpt-4o-mini"]`)
- `MODEL_BASE_URL` (optional for OpenAI-compatible endpoints)
- `EMBEDDINGS_MODEL_NAME` (e.g., `text-embedding-3-large`)
- `EMBEDDINGS_BASE_URL` (optional)
- `TAVILY_API_KEY` (for web search tool)

Auth and tokens:
- `TOKEN_BEARER_URL` (default `/api/v1/auth/login`)
- `JWT_SECRET` (use a strong, random value)
- `JWT_ALGORITHM` (e.g., `HS256`)
- `ACCESS_TOKEN_EXPIRY_MINS` (e.g., `1440`)
- `REFRESH_TOKEN_EXPIRY_DAYS` (e.g., `1`)

Database and vector store:
- `POSTGRES_HOST` (e.g., `127.0.0.1` or `postgres` in Docker)
- `POSTGRES_PORT` (e.g., `5432`)
- `POSTGRES_USER` (e.g., `postgres`)
- `POSTGRES_PASSWORD` (e.g., `test`)
- `POSTGRES_DATABASE` (e.g., `langgraph_db`)
- `PGVECTOR_COLLECTION_NAME` (e.g., `my_collection`)

Frontend:
- `BACKEND_BASE_URL` (e.g., `http://127.0.0.1:8000/api/v1` when running locally)

Example values are provided in `env.example`.

## 🧩 API Overview

Base URL: `/api/v1`

Auth:
- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/logout`
- `GET /auth/refresh-token`

Users:
- `GET /users/me`
- `PUT /users/user-profile/{user_id}`
- `DELETE /users/user-profile/{user_id}`

Threads:
- `POST /threads/` (create)
- `GET /threads/` (list)
- `GET /threads/{thread_id}` (get)
- `PATCH /threads/{thread_id}` (update title)
- `DELETE /threads/{thread_id}` (delete + cascade cleanup of memory and vectors)

Documents:
- `GET /documents/{thread_id}` (list)
- `POST /documents/upload/{thread_id}` (upload + async index)
- `DELETE /documents/{document_id}` (remove + delete chunks from pgvector)

Chat and streaming:
- `POST /chat/` (public streaming chat; no tools or memory)
- `POST /chat/{thread_id}` (authenticated streaming agent with tools + memory)
- `GET /chat/{thread_id}` (retrieve persisted chat history)

API docs:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

## 📡 Streaming Protocol

Both chat endpoints stream newline-delimited JSON events. Event types include:
- `llm_chunk`: incremental model output
- `tool_call`: tool name and arguments when the agent invokes a tool
- `tool_result`: tool output returned to the agent

Example stream (JSON lines):

```json
{"type":"tool_call","name":"retrieve_user_documents","args":{"query":"policy overview"}}
{"type":"tool_result","name":"retrieve_user_documents","content":"...retrieved text..."}
{"type":"llm_chunk","content":"Here is a summary of your policy..."}
```

## 🔄 Architecture

1. Ingestion & Indexing
   - PDF, DOCX, TXT loaders; chunking via `RecursiveCharacterTextSplitter`
   - Async indexing into pgvector using `langchain-postgres` with JSONB metadata

2. Retrieval
   - Semantic similarity search filtered by `thread_id` and `user_id`
   - Tool: `retrieve_user_documents` leverages the vector store retriever

3. Agent & Generation
   - LangGraph ReAct agent (`create_react_agent`) with tools (documents + Tavily)
   - Configurable models via `MODEL_NAMES`
   - End-to-end streaming

4. Memory
   - LangGraph Postgres checkpointer (async) stores per-thread chat histories
   - Thread deletion cleans up checkpointer state and related vector chunks

## 🖼️ Screenshots

### Unauthenticated Home Page
![home](./screenshots/home.png)

### Authenticated Home Page
![home-authenticated](./screenshots/home-authenticated.png)

## 📝 License

Licensed under the [MIT License](./LICENSE).

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a PR.


