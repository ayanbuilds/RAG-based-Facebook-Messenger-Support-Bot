from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Chunk:
    index: int
    text: str


def chunk_text(
    text: str,
    max_chars: int = 900,
    overlap_chars: int = 150,
) -> List[Chunk]:
    """
    Simple character-based chunking with overlap.
    Works well for MVP across PDF/DOCX/MD text.
    """
    text = (text or "").strip()
    if not text:
        return []

    chunks: List[Chunk] = []
    start = 0
    idx = 0

    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(Chunk(index=idx, text=chunk))
            idx += 1
        if end >= len(text):
            break
        start = max(0, end - overlap_chars)

    return chunks
