"""FastAPI service: ingest help content, answer widget questions."""
import os
import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app import bot

ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED = {".md", ".txt", ".pdf"}

app = FastAPI(title="Website Support Bot")
# Comma-separated list of sites allowed to embed the widget, e.g. https://shop.example.com
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=500)


@app.post("/ask")
def ask(q: Question):
    return bot.ask(q.question)


@app.post("/documents")
async def upload(file: UploadFile):
    # ponytail: no auth on upload; put it behind an API key or admin login before going public.
    name = Path(file.filename or "").name
    if Path(name).suffix.lower() not in ALLOWED:
        raise HTTPException(400, f"Supported types: {', '.join(sorted(ALLOWED))}")
    dest = UPLOAD_DIR / name
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"document": name, "chunks": bot.ingest(dest)}


@app.get("/widget.js")
def widget():
    return FileResponse(ROOT / "widget.js", media_type="application/javascript")


@app.get("/")
def demo():
    return FileResponse(ROOT / "demo.html")
