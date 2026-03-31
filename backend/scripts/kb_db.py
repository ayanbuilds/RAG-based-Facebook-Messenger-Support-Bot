from __future__ import annotations

from typing import Iterable, Optional, Tuple, List

from sqlalchemy import text
from sqlalchemy.orm import Session


def insert_document(db: Session, title: str, source: Optional[str], content: str) -> int:
    row = db.execute(
        text(
            """
            insert into kb_documents (title, source, content)
            values (:title, :source, :content)
            returning id
            """
        ),
        {"title": title, "source": source, "content": content},
    ).first()
    db.commit()
    return int(row[0])


def clear_document_chunks(db: Session, document_id: int) -> None:
    db.execute(
        text("delete from kb_chunks where document_id = :document_id"),
        {"document_id": document_id},
    )
    db.commit()


def insert_chunks(
    db: Session,
    document_id: int,
    chunks: List[Tuple[int, str, list]],
) -> None:
    """
    chunks: list of (chunk_index, chunk_text, embedding_list[float])
    """
    db.execute(
        text(
            """
            insert into kb_chunks (document_id, chunk_index, chunk_text, embedding)
            values (:document_id, :chunk_index, :chunk_text, :embedding)
            """
        ),
        [
            {
                "document_id": document_id,
                "chunk_index": idx,
                "chunk_text": ctext,
                # pgvector accepts array-like via SQLAlchemy text if casted
                "embedding": embedding,
            }
            for (idx, ctext, embedding) in chunks
        ],
    )
    db.commit()
