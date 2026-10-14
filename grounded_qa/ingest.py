"""Turn approved source documents into sections with metadata, ready for retrieval.

Sources are Markdown or plain-text files in a sources directory. Each file may start with a small header:

    ---
    title: Fact Sheet #28: The Family and Medical Leave Act
    source: https://www.dol.gov/...
    effective: 2023-02-01
    ---

Sections split on Markdown headings. Each section keeps the title, heading, source URL, effective date and
its position, which is what a citation points at.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, Field

_HEADER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_HEADING = re.compile(r"^(#{1,4})\s+(.*)$", re.MULTILINE)


class Section(BaseModel):
    id: str
    doc: str
    title: str
    heading: str
    text: str
    source: str | None = None
    effective: str | None = None
    embedding: list[float] | None = Field(default=None, repr=False)


def parse_doc(path: Path) -> list[Section]:
    raw = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    m = _HEADER.match(raw)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        raw = raw[m.end() :]
    title = meta.get("title", path.stem)
    sections: list[Section] = []
    positions = [(h.start(), h.group(2).strip()) for h in _HEADING.finditer(raw)]
    if not positions:
        positions = [(0, title)]
    for i, (start, heading) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(raw)
        body = _HEADING.sub("", raw[start:end], count=1).strip()
        if not body:
            continue
        sections.append(
            Section(
                id=f"{path.stem}#{i + 1}",
                doc=path.stem,
                title=title,
                heading=heading,
                text=body,
                source=meta.get("source"),
                effective=meta.get("effective"),
            )
        )
    return sections


def build_index(sources_dir: Path, out_path: Path, embed=None) -> list[Section]:
    """Parse every .md/.txt file under sources_dir, optionally embed, and write a JSON index."""
    sections: list[Section] = []
    for p in sorted(sources_dir.glob("**/*")):
        if p.suffix.lower() in (".md", ".txt") and p.name.lower() != "readme.md":
            sections.extend(parse_doc(p))
    if embed is not None and sections:
        vectors = embed([s.text for s in sections])
        for s, v in zip(sections, vectors, strict=True):
            s.embedding = v
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps([s.model_dump() for s in sections]), encoding="utf-8")
    return sections


def load_index(path: Path) -> list[Section]:
    return [Section.model_validate(s) for s in json.loads(path.read_text(encoding="utf-8"))]
