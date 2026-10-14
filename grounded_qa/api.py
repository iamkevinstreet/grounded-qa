"""Question service plus an approver-only admin API for the approved sources.

    uvicorn grounded_qa.api:app --reload

Roles for local development come from the X-Role header (requester | approver). Project 3 documents the
Entra ID integration that replaces the header.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from kds.llm.adapter import get_adapter
from kds.logs import get_logger, log_event, new_request_id
from pydantic import BaseModel

from grounded_qa.answer import Result, answer_question
from grounded_qa.ingest import build_index, load_index
from grounded_qa.retrieve import Retriever

_log = get_logger("qa.api")
DATA = Path(__file__).resolve().parent / "data"
SOURCES = DATA / "sources"
INDEX = DATA / "generated" / "index.json"

app = FastAPI(title="Grounded Q&A", version="0.1.0")
_retriever: Retriever | None = None


def retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        sections = (
            load_index(INDEX) if INDEX.exists() else build_index(SOURCES, INDEX, embed=get_adapter().embed)
        )
        _retriever = Retriever(sections, embed=get_adapter().embed)
    return _retriever


def require_role(role: str):
    def check(x_role: str = Header(default="requester")) -> str:
        if x_role != role:
            raise HTTPException(403, f"requires role {role}")
        return x_role

    return check


class Question(BaseModel):
    question: str
    k: int = 5
    mode: str = "hybrid"


@app.get("/health")
def health() -> dict:
    return {"ok": True, "sections": len(retriever().sections)}


@app.post("/ask", response_model=Result)
def ask(q: Question) -> Result:
    with new_request_id():
        return answer_question(get_adapter(), retriever(), q.question, k=q.k, mode=q.mode)


@app.get("/sources")
def list_sources() -> list[str]:
    return sorted(p.name for p in SOURCES.glob("*.md") if p.name.lower() != "readme.md")


class SourceIn(BaseModel):
    name: str
    content: str


@app.post("/sources", dependencies=[Depends(require_role("approver"))])
def add_source(src: SourceIn) -> dict:
    if "/" in src.name or not src.name.endswith(".md"):
        raise HTTPException(400, "name must be a .md file name")
    (SOURCES / src.name).write_text(src.content, encoding="utf-8")
    _reindex()
    log_event(_log, "sources.added", name=src.name, by="approver")
    return {"added": src.name, "sections": len(retriever().sections)}


@app.delete("/sources/{name}", dependencies=[Depends(require_role("approver"))])
def remove_source(name: str) -> dict:
    p = SOURCES / name
    if not p.exists():
        raise HTTPException(404, "no such source")
    p.unlink()
    _reindex()
    log_event(_log, "sources.removed", name=name, by="approver")
    return {"removed": name, "sections": len(retriever().sections)}


def _reindex() -> None:
    global _retriever
    _retriever = None
    if INDEX.exists():
        INDEX.unlink()
    retriever()
