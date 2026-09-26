import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="AI Meeting Summarizer", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:8000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ActionItem(BaseModel):
    task: str
    owner: str | None = None
    deadline: str | None = None

class MeetingResult(BaseModel):
    summary: str
    decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)

SYSTEM_PROMPT = """You summarize meeting transcripts. Return ONLY valid JSON with this shape:
{"summary":"...","decisions":["..."],"action_items":[{"task":"...","owner":"... or null","deadline":"... or null"}],"topics":["..."]}
Do not invent information. Use null when an owner or deadline is not stated."""

async def summarize_with_llm(transcript: str) -> MeetingResult:
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    if not api_key:
        raise HTTPException(status_code=503, detail="LLM_API_KEY is not configured")
    payload = {
        "model": model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return MeetingResult.model_validate(json.loads(content))
    except (httpx.HTTPError, KeyError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Unable to summarize transcript: {exc}") from exc

@app.get("/api/health")
async def health():
    return {"status": "ok", "llm_configured": bool(os.getenv("LLM_API_KEY"))}

@app.post("/api/summarize", response_model=MeetingResult)
async def summarize(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Please upload a .txt transcript")
    transcript = (await file.read()).decode("utf-8", errors="replace").strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="The transcript is empty")
    if len(transcript) > 200_000:
        raise HTTPException(status_code=413, detail="Transcript must be smaller than 200 KB")
    return await summarize_with_llm(transcript)

app.mount("/static", StaticFiles(directory=ROOT / "frontend"), name="static")

@app.get("/")
async def index():
    return FileResponse(ROOT / "frontend" / "index.html")
