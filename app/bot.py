"""Ingest FAQ/help content, retrieve, answer with a citation, or refuse."""
import hashlib
import os
import re
from pathlib import Path

import chromadb
from openai import OpenAI

DB_DIR = os.getenv("DB_DIR", "data/chroma")
TOP_K = int(os.getenv("TOP_K", "4"))
# Relevance gate: below this cosine similarity we don't even ask the LLM.
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.35"))
CHUNK_CHARS = 900

llm = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
    api_key=os.getenv("LLM_API_KEY", "not-needed-for-local"),
)
MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Chroma's built-in local embedding model (all-MiniLM-L6-v2), no embedding API needed.
collection = chromadb.PersistentClient(DB_DIR).get_or_create_collection(
    "faq", metadata={"hnsw:space": "cosine"}
)

NOT_FOUND = "Sorry, I couldn't find that in our help articles. Please contact our support team."

PROMPT = """You are a customer-support assistant for a business website.
Answer the customer's question using ONLY the numbered help-article excerpts below.
- Be brief and friendly (1-3 sentences).
- End each factual sentence with the excerpt number in square brackets. Valid numbers: {valid}.
- If the excerpts do not answer the question, reply exactly: "{not_found}"
- Never invent prices, dates, policies or contact details.

Excerpts:
{context}

Customer question: {question}"""


def sections(text: str) -> list[tuple[str, str]]:
    """Split markdown by headings so each chunk cites 'faq.md › Returns'."""
    out, heading, buf = [], "", []
    for line in text.splitlines():
        m = re.match(r"#{1,6}\s+(.*)", line)
        if m:
            if "".join(buf).strip():
                out.append((heading, "\n".join(buf)))
            heading, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    if "".join(buf).strip():
        out.append((heading, "\n".join(buf)))
    return out


def chunk(text: str) -> list[str]:
    # ponytail: fixed-size split for long sections; FAQ sections are usually short.
    text = " ".join(text.split())
    return [text[i:i + CHUNK_CHARS] for i in range(0, len(text), CHUNK_CHARS)]


def to_chunks(path: Path) -> list[dict]:
    if path.suffix.lower() == ".pdf":
        import pymupdf
        with pymupdf.open(path) as pdf:
            parts = [(f"page {i + 1}", p.get_text()) for i, p in enumerate(pdf)]
    else:
        parts = sections(path.read_text(errors="ignore"))
    return [
        {"text": c, "source": path.name, "location": loc}
        for loc, body in parts
        for c in chunk(f"{loc}\n{body}" if loc else body)  # heading text helps retrieval
    ]


def ingest(path: Path) -> int:
    chunks = to_chunks(path)
    collection.delete(where={"source": path.name})  # re-ingesting replaces the file
    if chunks:
        collection.add(
            ids=[hashlib.sha1(f"{path.name}:{i}:{c['text']}".encode()).hexdigest() for i, c in enumerate(chunks)],
            documents=[c["text"] for c in chunks],
            metadatas=[{"source": c["source"], "location": c["location"]} for c in chunks],
        )
    return len(chunks)


def retrieve(question: str) -> list[dict]:
    n = collection.count()
    if n == 0:
        return []
    res = collection.query(query_texts=[question], n_results=min(TOP_K, n))
    return [
        {"text": t, "source": m["source"], "location": m["location"], "score": round(1 - d, 3)}
        for t, m, d in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]


def ask(question: str) -> dict:
    hits = [h for h in retrieve(question) if h["score"] >= MIN_SCORE]
    if not hits:  # relevance gate: no LLM call, no cost, no chance to make something up
        return {"answer": NOT_FOUND, "sources": [], "gated": True}
    context = "\n\n".join(f"[{i}] ({h['source']} › {h['location']})\n{h['text']}" for i, h in enumerate(hits, 1))
    valid = ", ".join(f"[{i}]" for i in range(1, len(hits) + 1))
    r = llm.chat.completions.create(
        model=MODEL, temperature=0,
        messages=[{"role": "user", "content": PROMPT.format(valid=valid, not_found=NOT_FOUND, context=context, question=question)}],
    )
    answer = (r.choices[0].message.content or "").strip()
    cited = [hits[int(n) - 1] for n in dict.fromkeys(re.findall(r"\[(\d+)\]", answer)) if 0 < int(n) <= len(hits)]
    return {
        "answer": re.sub(r"\s*\[\d+\]", "", answer),  # widget shows sources separately
        "sources": [{"source": h["source"], "location": h["location"], "score": h["score"]} for h in cited],
        "gated": False,
    }


if __name__ == "__main__":  # python -m app.bot samples/*.md
    import sys
    for p in sys.argv[1:]:
        print(p, ingest(Path(p)), "chunks")
