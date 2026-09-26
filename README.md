# AI Meeting Summarizer

A minimal end-to-end protocol for turning `.txt` meeting transcripts into structured JSON.

## Flow

`Browser upload → POST /api/summarize → FastAPI validation → OpenAI-compatible LLM → Pydantic JSON → dashboard/download`

## Run locally

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cp .env.example .env
# Add your LLM_API_KEY to .env
uvicorn backend.main:app --reload
```

Open http://localhost:8000. The API also provides interactive documentation at `/docs`.

## API contract

`POST /api/summarize` accepts multipart form data with a `file` field containing a UTF-8 `.txt` file. It returns:

```json
{
  "summary": "...",
  "decisions": ["..."],
  "action_items": [{"task": "...", "owner": "...", "deadline": "..."}],
  "topics": ["..."]
}
```

The backend uses an OpenAI-compatible `/chat/completions` endpoint, so `LLM_BASE_URL` can point to another compatible provider. Never commit `.env` or API keys.
