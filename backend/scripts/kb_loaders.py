from __future__ import annotations

from pathlib import Path
from typing import List

from pypdf import PdfReader
from docx import Document


def load_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts: List[str] = []
    for page in reader.pages:
        t = page.extract_text() or ""
        if t.strip():
            parts.append(t)
    return "\n\n".join(parts).strip()


def load_docx_text(path: Path) -> str:
    doc = Document(str(path))
    parts: List[str] = []
    for p in doc.paragraphs:
        if p.text and p.text.strip():
            parts.append(p.text.strip())
    return "\n".join(parts).strip()


def load_md_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore").strip()


def load_text_by_extension(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return load_pdf_text(path)
    if ext in (".docx",):
        return load_docx_text(path)
    if ext in (".md", ".txt"):
        return load_md_text(path)
    raise ValueError(f"Unsupported file type: {ext}")
