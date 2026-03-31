from __future__ import annotations

from typing import List, Dict
from sqlalchemy import text
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model = SentenceTransformer(EMBED_MODEL_NAME)

def embed_query(q: str) -> list[float]:
    vec = _model.encode([q], normalize_embeddings=True)[0]
    return vec.tolist()

def retrieve_context(db: Session, query: str, top_k: int = 5) -> List[Dict]:
    qvec = embed_query(query)
    rows = db.execute(
        # text("select * from match_kb_chunks(:qvec, :k)"),
        text("select * from match_kb_chunks((:qvec)::vector(384), :k)"),
        {"qvec": qvec, "k": top_k},
    ).mappings().all()
    return [dict(r) for r in rows]
