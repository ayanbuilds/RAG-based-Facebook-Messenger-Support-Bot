# import time
# from sqlalchemy import select, text
# from sqlalchemy.orm import Session

# from app.db.session import SessionLocal
# from app.db.models import BotJob, Message, Conversation, Customer
# from app.services.groq_bot import build_reply
# from app.services.messenger_send import send_text_message

# POLL_SECONDS = 1.0
# MAX_ATTEMPTS = 3

# def lock_next_job(db: Session) -> BotJob | None:
#     # Use FOR UPDATE SKIP LOCKED to safely pick one job in concurrent workers
#     job = db.execute(
#         text("""
#         select * from bot_jobs
#         where status = 'queued'
#         order by created_at asc
#         limit 1
#         for update skip locked
#         """)
#     ).mappings().first()

#     if not job:
#         return None

#     # Load as ORM object
#     obj = db.get(BotJob, job["id"])
#     obj.status = "processing"
#     obj.locked_at = text("now()")  # DB side
#     obj.attempts = (obj.attempts or 0) + 1
#     db.commit()
#     db.refresh(obj)
#     return obj

# def run_once():
#     db = SessionLocal()
#     try:
#         job = lock_next_job(db)
#         if not job:
#             return

#         inbound = db.get(Message, job.inbound_message_id)
#         conv = db.get(Conversation, job.conversation_id)
#         customer = db.get(Customer, conv.customer_id) if conv else None

#         if not inbound or not customer:
#             job.status = "failed"
#             job.last_error = "Missing inbound message or customer"
#             db.commit()
#             return

#         user_text = inbound.content
#         reply_text = build_reply(user_text)

#         # Save outbound message
#         bot_msg = Message(
#             conversation_id=conv.id,
#             direction="outbound",
#             sender_type="bot",
#             content=reply_text,
#             platform_message_id=None
#         )
#         db.add(bot_msg)
#         db.commit()
#         db.refresh(bot_msg)

#         # Send to Facebook
#         send_text_message(customer.psid, reply_text)

#         job.status = "done"
#         job.last_error = None
#         db.commit()

#     except Exception as e:
#         db.rollback()
#         # mark job failed if too many attempts
#         if "job" in locals() and job:
#             job.last_error = str(e)
#             if job.attempts >= MAX_ATTEMPTS:
#                 job.status = "failed"
#             else:
#                 job.status = "queued"
#             db.commit()
#         print(f"[Worker error] {e}")
#     finally:
#         db.close()

# def main():
#     print("Worker started...")
#     while True:
#         run_once()
#         time.sleep(POLL_SECONDS)

# if __name__ == "__main__":
#     main()


# edit 2
# import os
# import time
# from typing import Optional

# from sqlalchemy import text
# from sqlalchemy.orm import Session

# from app.db.session import SessionLocal
# from app.db.models import BotJob, Message, Conversation, Customer
# from app.services.groq_bot import build_reply
# from app.services.messenger_send import send_text_message

# POLL_SECONDS = float(os.getenv("WORKER_POLL_SECONDS", "1.0"))
# MAX_ATTEMPTS = int(os.getenv("WORKER_MAX_ATTEMPTS", "3"))


# def _lock_next_job(db: Session) -> Optional[int]:
#     """
#     Atomically lock one queued job using FOR UPDATE SKIP LOCKED.
#     Returns job_id or None.
#     """
#     row = db.execute(
#         text(
#             """
#             select id
#             from bot_jobs
#             where status = 'queued'
#             order by created_at asc
#             limit 1
#             for update skip locked
#             """
#         )
#     ).first()

#     if not row:
#         return None

#     job_id = int(row[0])

#     db.execute(
#         text(
#             """
#             update bot_jobs
#             set status = 'processing',
#                 locked_at = now(),
#                 attempts = attempts + 1,
#                 updated_at = now()
#             where id = :job_id
#             """
#         ),
#         {"job_id": job_id},
#     )
#     db.commit()
#     return job_id


# def _mark_job_done(db: Session, job_id: int) -> None:
#     db.execute(
#         text(
#             """
#             update bot_jobs
#             set status = 'done',
#                 last_error = null,
#                 updated_at = now()
#             where id = :job_id
#             """
#         ),
#         {"job_id": job_id},
#     )
#     db.commit()


# def _mark_job_failed(db: Session, job_id: int, err: str, attempts: int) -> None:
#     status = "failed" if attempts >= MAX_ATTEMPTS else "queued"
#     db.execute(
#         text(
#             """
#             update bot_jobs
#             set status = :status,
#                 last_error = :err,
#                 updated_at = now()
#             where id = :job_id
#             """
#         ),
#         {"status": status, "err": err[:2000], "job_id": job_id},
#     )
#     db.commit()


# def run_once() -> None:
#     db = SessionLocal()
#     try:
#         job_id = _lock_next_job(db)
#         if not job_id:
#             return

#         job = db.get(BotJob, job_id)
#         if not job:
#             return

#         inbound = db.get(Message, job.inbound_message_id)
#         conv = db.get(Conversation, job.conversation_id)

#         if not inbound or not conv:
#             _mark_job_failed(db, job_id, "Missing inbound message or conversation", attempts=job.attempts)
#             return

#         customer = db.get(Customer, conv.customer_id)
#         if not customer:
#             _mark_job_failed(db, job_id, "Missing customer", attempts=job.attempts)
#             return

#         user_text = inbound.content
#         reply_text = build_reply(user_text)

#         # Save outbound message
#         bot_msg = Message(
#             conversation_id=conv.id,
#             direction="outbound",
#             sender_type="bot",
#             content=reply_text,
#             platform_message_id=None,
#         )
#         db.add(bot_msg)
#         db.commit()
#         db.refresh(bot_msg)

#         # Send to Messenger
#         send_text_message(customer.psid, reply_text)

#         _mark_job_done(db, job_id)

#     except Exception as e:
#         db.rollback()
#         # If something went wrong after locking, try to mark failed/requeue.
#         try:
#             if "job_id" in locals() and job_id:
#                 job = db.get(BotJob, job_id)
#                 attempts = job.attempts if job else MAX_ATTEMPTS
#                 _mark_job_failed(db, job_id, str(e), attempts=attempts)
#         except Exception:
#             db.rollback()
#         print(f"[Worker Error] {e}")
#     finally:
#         db.close()


# def main() -> None:
#     print("Worker started.")
#     while True:
#         run_once()
#         time.sleep(POLL_SECONDS)


# if __name__ == "__main__":
#     main()


# edit 3
# import os
# import time
# from typing import Optional

# from sqlalchemy import text
# from sqlalchemy.orm import Session

# from app.db.session import SessionLocal
# from app.db.models import BotJob, Message, Conversation, Customer
# from app.services.groq_bot import build_reply
# from app.services.messenger_send import send_text_message
# from app.rag.retriever import retrieve_context

# POLL_SECONDS = float(os.getenv("WORKER_POLL_SECONDS", "1.0"))
# MAX_ATTEMPTS = int(os.getenv("WORKER_MAX_ATTEMPTS", "3"))


# def _lock_next_job(db: Session) -> Optional[int]:
#     """
#     Atomically lock one queued job using FOR UPDATE SKIP LOCKED.
#     Returns job_id or None.
#     """
#     row = db.execute(
#         text(
#             """
#             select id
#             from bot_jobs
#             where status = 'queued'
#             order by created_at asc
#             limit 1
#             for update skip locked
#             """
#         )
#     ).first()

#     if not row:
#         return None

#     job_id = int(row[0])

#     db.execute(
#         text(
#             """
#             update bot_jobs
#             set status = 'processing',
#                 locked_at = now(),
#                 attempts = attempts + 1,
#                 updated_at = now()
#             where id = :job_id
#             """
#         ),
#         {"job_id": job_id},
#     )
#     db.commit()
#     return job_id


# def _mark_job_done(db: Session, job_id: int) -> None:
#     db.execute(
#         text(
#             """
#             update bot_jobs
#             set status = 'done',
#                 last_error = null,
#                 updated_at = now()
#             where id = :job_id
#             """
#         ),
#         {"job_id": job_id},
#     )
#     db.commit()


# def _mark_job_failed(db: Session, job_id: int, err: str, attempts: int) -> None:
#     status = "failed" if attempts >= MAX_ATTEMPTS else "queued"
#     db.execute(
#         text(
#             """
#             update bot_jobs
#             set status = :status,
#                 last_error = :err,
#                 updated_at = now()
#             where id = :job_id
#             """
#         ),
#         {"status": status, "err": err[:2000], "job_id": job_id},
#     )
#     db.commit()


# def run_once() -> None:
#     db = SessionLocal()
#     try:
#         job_id = _lock_next_job(db)
#         if not job_id:
#             return

#         job = db.get(BotJob, job_id)
#         if not job:
#             return

#         inbound = db.get(Message, job.inbound_message_id)
#         conv = db.get(Conversation, job.conversation_id)

#         if not inbound or not conv:
#             _mark_job_failed(db, job_id, "Missing inbound message or conversation", attempts=job.attempts)
#             return

#         customer = db.get(Customer, conv.customer_id)
#         if not customer:
#             _mark_job_failed(db, job_id, "Missing customer", attempts=job.attempts)
#             return

#         user_text = inbound.content
        
#         # Retrieve relevant context from RAG
#         matches = retrieve_context(db, user_text, top_k=5)
#         context_chunks = [m["chunk_text"] for m in matches]
#         reply_text = build_reply(user_text, context_chunks)

#         # Save outbound message
#         bot_msg = Message(
#             conversation_id=conv.id,
#             direction="outbound",
#             sender_type="bot",
#             content=reply_text,
#             platform_message_id=None,
#         )
#         db.add(bot_msg)
#         db.commit()
#         db.refresh(bot_msg)

#         # Send to Messenger
#         send_text_message(customer.psid, reply_text)

#         _mark_job_done(db, job_id)

#     except Exception as e:
#         db.rollback()
#         # If something went wrong after locking, try to mark failed/requeue.
#         try:
#             if "job_id" in locals() and job_id:
#                 job = db.get(BotJob, job_id)
#                 attempts = job.attempts if job else MAX_ATTEMPTS
#                 _mark_job_failed(db, job_id, str(e), attempts=attempts)
#         except Exception:
#             db.rollback()
#         print(f"[Worker Error] {e}")
#     finally:
#         db.close()


# def main() -> None:
#     print("Worker started.")
#     while True:
#         run_once()
#         time.sleep(POLL_SECONDS)


# if __name__ == "__main__":
#     main()

# edit 4

# import os
# import time
# from typing import Optional

# from sqlalchemy import text
# from sqlalchemy.orm import Session

# from app.db.session import SessionLocal
# from app.db.models import BotJob, Message, Conversation, Customer
# from app.services.groq_bot import build_reply
# from app.services.messenger_send import send_text_message
# from app.rag.retriever import retrieve_context
# from app.services.handoff import wants_human

# POLL_SECONDS = float(os.getenv("WORKER_POLL_SECONDS", "1.0"))
# MAX_ATTEMPTS = int(os.getenv("WORKER_MAX_ATTEMPTS", "3"))


# def _lock_next_job(db: Session) -> Optional[int]:
#     """
#     Atomically lock one queued job using FOR UPDATE SKIP LOCKED.
#     Returns job_id or None.
#     """
#     row = db.execute(
#         text(
#             """
#             select id
#             from bot_jobs
#             where status = 'queued'
#             order by created_at asc
#             limit 1
#             for update skip locked
#             """
#         )
#     ).first()

#     if not row:
#         return None

#     job_id = int(row[0])

#     db.execute(
#         text(
#             """
#             update bot_jobs
#             set status = 'processing',
#                 locked_at = now(),
#                 attempts = attempts + 1,
#                 updated_at = now()
#             where id = :job_id
#             """
#         ),
#         {"job_id": job_id},
#     )
#     db.commit()
#     return job_id


# def _mark_job_done(db: Session, job_id: int) -> None:
#     db.execute(
#         text(
#             """
#             update bot_jobs
#             set status = 'done',
#                 last_error = null,
#                 updated_at = now()
#             where id = :job_id
#             """
#         ),
#         {"job_id": job_id},
#     )
#     db.commit()


# def _mark_job_failed(db: Session, job_id: int, err: str, attempts: int) -> None:
#     status = "failed" if attempts >= MAX_ATTEMPTS else "queued"
#     db.execute(
#         text(
#             """
#             update bot_jobs
#             set status = :status,
#                 last_error = :err,
#                 updated_at = now()
#             where id = :job_id
#             """
#         ),
#         {"status": status, "err": err[:2000], "job_id": job_id},
#     )
#     db.commit()


# def run_once() -> None:
#     db = SessionLocal()
#     try:
#         job_id = _lock_next_job(db)
#         if not job_id:
#             return

#         job = db.get(BotJob, job_id)
#         if not job:
#             return

#         inbound = db.get(Message, job.inbound_message_id)
#         conv = db.get(Conversation, job.conversation_id)

#         if not inbound or not conv:
#             _mark_job_failed(db, job_id, "Missing inbound message or conversation", attempts=job.attempts)
#             return

#         customer = db.get(Customer, conv.customer_id)
#         if not customer:
#             _mark_job_failed(db, job_id, "Missing customer", attempts=job.attempts)
#             return

#         user_text = inbound.content

#         # A) If conversation is already NEEDS_HUMAN → skip AI
#         if conv.status == "NEEDS_HUMAN":
#             _mark_job_done(db, job_id)
#             return

#         # B) If user asked for human → set NEEDS_HUMAN + acknowledge + stop AI
#         if wants_human(user_text):
#             db.execute(
#                 text("update conversations set status='NEEDS_HUMAN', updated_at=now() where id=:cid"),
#                 {"cid": conv.id},
#             )
#             db.commit()

#             ack = "A human assistant will respond shortly."

#             bot_msg = Message(
#                 conversation_id=conv.id,
#                 direction="outbound",
#                 sender_type="bot",
#                 content=ack,
#                 platform_message_id=None,
#             )
#             db.add(bot_msg)
#             db.commit()
#             db.refresh(bot_msg)

#             send_text_message(customer.psid, ack)

#             _mark_job_done(db, job_id)
#             return
        
#         # Retrieve relevant context from RAG
#         matches = retrieve_context(db, user_text, top_k=5)
#         context_chunks = [m["chunk_text"] for m in matches]
#         reply_text = build_reply(user_text, context_chunks)

#         # Save outbound message
#         bot_msg = Message(
#             conversation_id=conv.id,
#             direction="outbound",
#             sender_type="bot",
#             content=reply_text,
#             platform_message_id=None,
#         )
#         db.add(bot_msg)
#         db.commit()
#         db.refresh(bot_msg)

#         # Send to Messenger
#         send_text_message(customer.psid, reply_text)

#         _mark_job_done(db, job_id)

#     except Exception as e:
#         db.rollback()
#         # If something went wrong after locking, try to mark failed/requeue.
#         try:
#             if "job_id" in locals() and job_id:
#                 job = db.get(BotJob, job_id)
#                 attempts = job.attempts if job else MAX_ATTEMPTS
#                 _mark_job_failed(db, job_id, str(e), attempts=attempts)
#         except Exception:
#             db.rollback()
#         print(f"[Worker Error] {e}")
#     finally:
#         db.close()


# def main() -> None:
#     print("Worker started.")
#     while True:
#         run_once()
#         time.sleep(POLL_SECONDS)


# if __name__ == "__main__":
#     main()

# edit 5

import os
import time
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import BotJob, Message, Conversation, Customer
from app.services.groq_bot import build_reply
from app.services.messenger_send import send_text_message
from app.rag.retriever import retrieve_context
from app.services.handoff import wants_human

POLL_SECONDS = float(os.getenv("WORKER_POLL_SECONDS", "1.0"))
MAX_ATTEMPTS = int(os.getenv("WORKER_MAX_ATTEMPTS", "3"))


def _lock_next_job(db: Session) -> Optional[int]:
    """
    Atomically lock one queued job using FOR UPDATE SKIP LOCKED.
    Returns job_id or None.
    """
    row = db.execute(
        text(
            """
            select id
            from bot_jobs
            where status = 'queued'
            order by created_at asc
            limit 1
            for update skip locked
            """
        )
    ).first()

    if not row:
        return None

    job_id = int(row[0])

    db.execute(
        text(
            """
            update bot_jobs
            set status = 'processing',
                locked_at = now(),
                attempts = attempts + 1,
                updated_at = now()
            where id = :job_id
            """
        ),
        {"job_id": job_id},
    )
    db.commit()
    return job_id


def _mark_job_done(db: Session, job_id: int) -> None:
    db.execute(
        text(
            """
            update bot_jobs
            set status = 'done',
                last_error = null,
                updated_at = now()
            where id = :job_id
            """
        ),
        {"job_id": job_id},
    )
    db.commit()


def _mark_job_failed(db: Session, job_id: int, err: str, attempts: int) -> None:
    status = "failed" if attempts >= MAX_ATTEMPTS else "queued"
    db.execute(
        text(
            """
            update bot_jobs
            set status = :status,
                last_error = :err,
                updated_at = now()
            where id = :job_id
            """
        ),
        {"status": status, "err": err[:2000], "job_id": job_id},
    )
    db.commit()


def run_once() -> None:
    db = SessionLocal()
    try:
        job_id = _lock_next_job(db)
        if not job_id:
            return

        job = db.get(BotJob, job_id)
        if not job:
            return

        inbound = db.get(Message, job.inbound_message_id)
        conv = db.get(Conversation, job.conversation_id)

        if not inbound or not conv:
            _mark_job_failed(db, job_id, "Missing inbound message or conversation", attempts=job.attempts)
            return

        customer = db.get(Customer, conv.customer_id)
        if not customer:
            _mark_job_failed(db, job_id, "Missing customer", attempts=job.attempts)
            return

        user_text = inbound.content

        # Auto-reopen: if a resolved conversation receives a new message, activate the bot again
        if conv.status == "RESOLVED":
            db.execute(
                text("update conversations set status='BOT_ACTIVE', updated_at=now() where id=:cid"),
                {"cid": conv.id},
            )
            db.commit()
            conv.status = "BOT_ACTIVE"

        # A) If conversation is already NEEDS_HUMAN → skip AI
        if conv.status == "NEEDS_HUMAN":
            _mark_job_done(db, job_id)
            return

        # B) If user asked for human → set NEEDS_HUMAN + acknowledge + stop AI
        if wants_human(user_text):
            db.execute(
                text("update conversations set status='NEEDS_HUMAN', updated_at=now() where id=:cid"),
                {"cid": conv.id},
            )
            db.commit()

            ack = "A human assistant will respond shortly."

            bot_msg = Message(
                conversation_id=conv.id,
                direction="outbound",
                sender_type="bot",
                content=ack,
                platform_message_id=None,
            )
            db.add(bot_msg)
            db.commit()
            db.refresh(bot_msg)

            send_text_message(customer.psid, ack)

            _mark_job_done(db, job_id)
            return
        
        # Retrieve relevant context from RAG
        matches = retrieve_context(db, user_text, top_k=5)
        context_chunks = [m["chunk_text"] for m in matches]
        reply_text = build_reply(user_text, context_chunks)

        # Save outbound message
        bot_msg = Message(
            conversation_id=conv.id,
            direction="outbound",
            sender_type="bot",
            content=reply_text,
            platform_message_id=None,
        )
        db.add(bot_msg)
        db.commit()
        db.refresh(bot_msg)

        # Send to Messenger
        send_text_message(customer.psid, reply_text)

        _mark_job_done(db, job_id)

    except Exception as e:
        db.rollback()
        # If something went wrong after locking, try to mark failed/requeue.
        try:
            if "job_id" in locals() and job_id:
                job = db.get(BotJob, job_id)
                attempts = job.attempts if job else MAX_ATTEMPTS
                _mark_job_failed(db, job_id, str(e), attempts=attempts)
        except Exception:
            db.rollback()
        print(f"[Worker Error] {e}")
    finally:
        db.close()


def main() -> None:
    print("Worker started.")
    while True:
        run_once()
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()