# Citizen Helper

Citizen Helper is an AI-powered legal assistant for Vietnamese legal questions. It combines:
- A `FastAPI` backend for chat inference
- A `React + Vite` frontend chat interface
- A legal data pipeline (crawler + cleaning/indexing scripts)
- Cloud retrieval and generation using `Pinecone` + `Gemini`

## Project Overview

The system has 3 major layers:

1. `frontend/`
- Web client for users to send legal questions and receive AI answers.
- Calls backend endpoint: `POST http://localhost:8000/api/chat`.

2. `main.py` + `ai/ai_engine/core_engine.py`
- `main.py` starts a FastAPI server and initializes the AI engine at startup.
- `core_engine.py` loads embeddings, connects to Pinecone, queries relevant context, and asks Gemini to generate a response.

3. `ai/crawler/` and `ai/ai_engine/cleaning/`
- Crawler scripts collect legal documents from multiple sources.
- Cleaning/indexing scripts prepare and maintain legal datasets/vector resources.

## Tech Stack

- Backend: `Python`, `FastAPI`, `Uvicorn`
- AI/RAG: `LangChain`, `Pinecone`, `Google Gemini`, `HuggingFace embeddings`
- Frontend: `React`, `Vite`, `Tailwind CSS`

## Prerequisites

- Python `3.10+` (recommended: `3.11`)
- Node.js `18+`
- `pip` and `npm`
- API keys:
    - `PINECONE_API_KEY`
    - `GOOGLE_API_KEY`

## Setup

### 1. Create and activate Python environment

Windows PowerShell:

```powershell
python -m venv env
env\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv env
source env/bin/activate
```

### 2. Install backend dependencies

```bash
pip install -r requirements.txt
```

If you get a missing `dotenv` module error, install:

```bash
pip install python-dotenv
```

### 3. Create environment variables

Create a `.env` file in the project root:

```env
PINECONE_API_KEY=your_pinecone_api_key
GOOGLE_API_KEY=your_google_api_key
```

## Run the Project

### 1. Start backend API

From project root:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API docs: `http://localhost:8000/docs`

### 2. Start frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown by Vite (usually `http://localhost:5173`).

## API Reference

### `POST /api/chat`

Request body:

```json
{
    "message": "Tôi bị phạt giao thông trong trường hợp ..."
}
```

Response:

```json
{
    "response": "..."
}
```

## Data Pipeline and Crawlers

Crawler scripts are in `ai/crawler/`.

Examples:

```bash
python ai/crawler/vbpl_crawler.py
python ai/crawler/moj_crawler.py
python ai/crawler/thuvienphapluat_crawler.py
```

Processing/indexing scripts are in `ai/ai_engine/cleaning/`.

Examples:

```bash
python ai/ai_engine/cleaning/noise_cleaning.py
python ai/ai_engine/cleaning/process_data.py
python ai/ai_engine/cleaning/index_to_faiss.py
```

Run these scripts only when you need to refresh or rebuild the legal data resources.

## Project Structure

```text
citizen_helper/
|-- main.py
|-- requirements.txt
|-- ai/
|   |-- ai_engine/
|   |   |-- core_engine.py
|   |   |-- cleaning/
|   |   `-- citizen_helper_brain/
|   |-- crawler/
|   `-- check.py
`-- frontend/
        |-- src/
        |-- package.json
        `-- vite.config.js
```

## Troubleshooting

- Backend starts but chat fails:
    - Check `.env` keys.
    - Ensure your Pinecone index name matches the configured value in `ai/ai_engine/core_engine.py`.

- Frontend cannot call backend:
    - Confirm backend is running on port `8000`.
    - Confirm frontend is calling `http://localhost:8000/api/chat`.

- Slow first request:
    - Initial startup loads embedding and cloud clients; first request can be slower.

## Notes

- Keep secrets out of source code and use `.env` for all API keys.
- Large generated datasets/index files should stay out of git where possible.
