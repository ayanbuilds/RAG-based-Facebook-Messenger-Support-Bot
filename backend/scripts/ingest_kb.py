from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple

from tqdm import tqdm
from sentence_transformers import SentenceTransformer

from app.db.session import SessionLocal
from scripts.kb_loaders import load_text_by_extension
from scripts.kb_chunker import chunk_text
from scripts.kb_db import insert_document, clear_document_chunks, insert_chunks


EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dims


def iter_files(path: Path) -> List[Path]:
    if path.is_file():
        return [path]
    files: List[Path] = []
    for ext in ("*.pdf", "*.docx", "*.md", "*.txt"):
        files.extend(path.rglob(ext))
    return sorted(set(files))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="File or folder path containing PDF/DOCX/MD/TXT")
    parser.add_argument("--title", default=None, help="Optional document title (only used when --path is a file)")
    parser.add_argument("--source", default=None, help="Optional source label (e.g., 'company_docs')")
    parser.add_argument("--reindex", action="store_true", help="If set, deletes existing chunks for the document before inserting")
    args = parser.parse_args()

    target = Path(args.path).resolve()
    files = iter_files(target)

    if not files:
        raise SystemExit(f"No supported files found at: {target}")

    model = SentenceTransformer(EMBED_MODEL_NAME)

    db = SessionLocal()
    try:
        for fp in files:
            title = args.title if (args.title and fp.is_file() and fp == target) else fp.stem
            source = args.source or str(fp)

            text = load_text_by_extension(fp)
            if not text.strip():
                print(f"[skip] empty text: {fp}")
                continue

            # Insert document
            doc_id = insert_document(db, title=title, source=source, content=text)

            if args.reindex:
                clear_document_chunks(db, doc_id)

            # Chunk
            chunks = chunk_text(text, max_chars=900, overlap_chars=150)
            if not chunks:
                print(f"[skip] no chunks: {fp}")
                continue

            # Embed chunks
            chunk_texts = [c.text for c in chunks]
            embeddings = model.encode(chunk_texts, normalize_embeddings=True, show_progress_bar=False)

            payload: List[Tuple[int, str, list]] = []
            for c, emb in zip(chunks, embeddings):
                payload.append((c.index, c.text, emb.tolist()))

            insert_chunks(db, document_id=doc_id, chunks=payload)
            print(f"[ok] ingested: {fp} -> doc_id={doc_id} chunks={len(payload)}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
