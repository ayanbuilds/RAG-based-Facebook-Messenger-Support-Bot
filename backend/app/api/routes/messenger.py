# import hmac
# import hashlib
# import json
# from typing import Any, Dict

# from fastapi import APIRouter, Request, HTTPException, Depends
# from sqlalchemy.orm import Session
# from sqlalchemy import select

# from app.core.config import settings
# from app.db.session import get_db
# from app.db.models import Customer, Conversation, Message
# from app.realtime.broker import broker
# from app.services.groq_bot import build_reply
# from app.services.messenger_send import send_text_message

# router = APIRouter(prefix="/webhook", tags=["messenger"])

# def verify_signature(app_secret: str, signature: str, body: bytes) -> bool:
#     """
#     Meta sends: X-Hub-Signature-256: sha256=<hash>
#     We compute HMAC SHA256 of request body using app secret and compare.
#     """
#     if not signature or not signature.startswith("sha256="):
#         return False
#     sig_hash = signature.split("=", 1)[1]
#     mac = hmac.new(app_secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
#     expected = mac.hexdigest()
#     return hmac.compare_digest(expected, sig_hash)

# @router.get("")
# async def webhook_verify(request: Request):
#     """
#     Meta verification:
#     GET /webhook?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...
#     """
#     params = request.query_params
#     mode = params.get("hub.mode")
#     token = params.get("hub.verify_token")
#     challenge = params.get("hub.challenge")

#     if mode == "subscribe" and token == settings.FB_VERIFY_TOKEN:
#         return int(challenge)
#     raise HTTPException(status_code=403, detail="Verification failed")

# @router.post("")
# async def webhook_receive(request: Request, db: Session = Depends(get_db)):
#     raw_body = await request.body()

#     # debug
#     print("Webhook POST received")
#     print("Headers:", dict(request.headers))
#     print("Raw body:", raw_body.decode("utf-8")[:500])

#     # Signature validation (important for security)
#     sig = request.headers.get("x-hub-signature-256", "")
#     if settings.FB_APP_SECRET:
#         if not verify_signature(settings.FB_APP_SECRET, sig, raw_body):
#             raise HTTPException(status_code=403, detail="Invalid signature")

#     payload: Dict[str, Any] = json.loads(raw_body.decode("utf-8"))

#     # Messenger payload structure: entry -> messaging[]
#     if payload.get("object") != "page":
#         return {"ok": True}

#     for entry in payload.get("entry", []):
#         for event in entry.get("messaging", []):
#             sender = event.get("sender", {}).get("id")  # PSID
#             message = event.get("message", {})
#             text = message.get("text")

#             # Ignore echoes (messages sent by Page itself), to avoid infinite loops
#             if message.get("is_echo"):
#                 continue

#             # ignore non-text for MVP
#             if not sender or not text:
#                 continue

#             # 1) find/create customer
#             customer = db.execute(select(Customer).where(Customer.psid == sender)).scalar_one_or_none()
#             if not customer:
#                 customer = Customer(psid=sender)
#                 db.add(customer)
#                 db.commit()
#                 db.refresh(customer)

#             # 2) find/create conversation (1 customer = 1 conv)
#             conv = db.execute(select(Conversation).where(Conversation.customer_id == customer.id)).scalar_one_or_none()
#             if not conv:
#                 conv = Conversation(customer_id=customer.id, status="BOT_ACTIVE")
#                 db.add(conv)
#                 db.commit()
#                 db.refresh(conv)

#             # 3) save inbound message
#             msg = Message(conversation_id=conv.id, direction="inbound", sender_type="customer", content=text)
#             db.add(msg)
#             db.commit()
#             db.refresh(msg)

#             # 4) publish realtime event (Agent dashboard live update)
#             await broker.publish(conv.id, {
#                 "id": msg.id,
#                 "direction": msg.direction,
#                 "sender_type": msg.sender_type,
#                 "content": msg.content,
#                 "created_at": msg.created_at.isoformat() if msg.created_at else None
#             })

#             # 5) generate bot reply
#             try:
#                 reply_text = build_reply(text)

#                 bot_msg = Message(
#                     conversation_id=conv.id,
#                     direction="outbound",
#                     sender_type="bot",
#                     content=reply_text,
#                 )
#                 db.add(bot_msg)
#                 db.commit()
#                 db.refresh(bot_msg)

#                 await broker.publish(conv.id, {
#                     "id": bot_msg.id,
#                     "direction": bot_msg.direction,
#                     "sender_type": bot_msg.sender_type,
#                     "content": bot_msg.content,
#                     "created_at": bot_msg.created_at.isoformat() if bot_msg.created_at else None
#                 })

#                 send_text_message(sender, reply_text)

#             except Exception as e:
#                 # Do not crash the webhook; just log the failure.
#                 print(f"[Bot Pipeline Error] {e}")


#     return {"ok": True}


# edit 2

# import hmac
# import hashlib
# import json
# from typing import Any, Dict

# from fastapi import APIRouter, Request, HTTPException, Depends
# from sqlalchemy.orm import Session
# from sqlalchemy import select

# from app.core.config import settings
# from app.db.session import get_db
# from app.db.models import Customer, Conversation, Message
# from app.realtime.broker import broker
# from app.services.groq_bot import build_reply
# from app.services.messenger_send import send_text_message

# from app.db.models import BotJob


# router = APIRouter(prefix="/webhook", tags=["messenger"])

# def verify_signature(app_secret: str, signature: str, body: bytes) -> bool:
#     """
#     Meta sends: X-Hub-Signature-256: sha256=<hash>
#     We compute HMAC SHA256 of request body using app secret and compare.
#     """
#     if not signature or not signature.startswith("sha256="):
#         return False
#     sig_hash = signature.split("=", 1)[1]
#     mac = hmac.new(app_secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
#     expected = mac.hexdigest()
#     return hmac.compare_digest(expected, sig_hash)

# @router.get("")
# async def webhook_verify(request: Request):
#     """
#     Meta verification:
#     GET /webhook?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...
#     """
#     params = request.query_params
#     mode = params.get("hub.mode")
#     token = params.get("hub.verify_token")
#     challenge = params.get("hub.challenge")

#     if mode == "subscribe" and token == settings.FB_VERIFY_TOKEN:
#         return int(challenge)
#     raise HTTPException(status_code=403, detail="Verification failed")

# @router.post("")
# async def webhook_receive(request: Request, db: Session = Depends(get_db)):
#     raw_body = await request.body()

#     # debug
#     print("Webhook POST received")
#     print("Headers:", dict(request.headers))
#     print("Raw body:", raw_body.decode("utf-8")[:500])

#     # Signature validation (important for security)
#     sig = request.headers.get("x-hub-signature-256", "")
#     if settings.FB_APP_SECRET:
#         if not verify_signature(settings.FB_APP_SECRET, sig, raw_body):
#             raise HTTPException(status_code=403, detail="Invalid signature")

#     payload: Dict[str, Any] = json.loads(raw_body.decode("utf-8"))

#     # Messenger payload structure: entry -> messaging[]
#     if payload.get("object") != "page":
#         return {"ok": True}

#     for entry in payload.get("entry", []):
#         for event in entry.get("messaging", []):
#             sender = event.get("sender", {}).get("id")  # PSID
#             message = event.get("message", {})
#             text = message.get("text")
#             mid = message.get("mid")

#             # Ignore echoes (messages sent by Page itself), to avoid infinite loops
#             if message.get("is_echo"):
#                 continue

#             # ignore non-text for MVP
#             if not sender or not text:
#                 continue

#             # Check for duplicate message delivery
#             if mid:
#                 existing = db.execute(
#                     select(Message).where(Message.platform_message_id == mid)
#                 ).scalar_one_or_none()
#                 if existing:
#                     # Duplicate delivery from Meta, ignore
#                     continue

#             # 1) find/create customer
#             customer = db.execute(select(Customer).where(Customer.psid == sender)).scalar_one_or_none()
#             if not customer:
#                 customer = Customer(psid=sender)
#                 db.add(customer)
#                 db.commit()
#                 db.refresh(customer)

#             # 2) find/create conversation (1 customer = 1 conv)
#             conv = db.execute(select(Conversation).where(Conversation.customer_id == customer.id)).scalar_one_or_none()
#             if not conv:
#                 conv = Conversation(customer_id=customer.id, status="BOT_ACTIVE")
#                 db.add(conv)
#                 db.commit()
#                 db.refresh(conv)

#             # 3) save inbound message
#             msg = Message(
#                 conversation_id=conv.id,
#                 direction="inbound",
#                 sender_type="customer",
#                 content=text,
#                 platform_message_id=mid
#             )
#             db.add(msg)
#             db.commit()
#             db.refresh(msg)

#             # 4) publish realtime event (Agent dashboard live update)
#             await broker.publish(conv.id, {
#                 "id": msg.id,
#                 "direction": msg.direction,
#                 "sender_type": msg.sender_type,
#                 "content": msg.content,
#                 "created_at": msg.created_at.isoformat() if msg.created_at else None
#             })

#             # 5) generate bot reply
#             try:
#                 reply_text = build_reply(text)

#                 bot_msg = Message(
#                     conversation_id=conv.id,
#                     direction="outbound",
#                     sender_type="bot",
#                     content=reply_text,
#                 )
#                 db.add(bot_msg)
#                 db.commit()
#                 db.refresh(bot_msg)

#                 await broker.publish(conv.id, {
#                     "id": bot_msg.id,
#                     "direction": bot_msg.direction,
#                     "sender_type": bot_msg.sender_type,
#                     "content": bot_msg.content,
#                     "created_at": bot_msg.created_at.isoformat() if bot_msg.created_at else None
#                 })

#                 send_text_message(sender, reply_text)

#             except Exception as e:
#                 # Do not crash the webhook; just log the failure.
#                 print(f"[Bot Pipeline Error] {e}")


#     return {"ok": True}

# edit 3

# import hmac
# import hashlib
# import json
# from typing import Any, Dict

# from fastapi import APIRouter, Request, HTTPException, Depends
# from sqlalchemy.orm import Session
# from sqlalchemy import select

# from app.core.config import settings
# from app.db.session import get_db
# from app.db.models import Customer, Conversation, Message, BotJob
# from app.realtime.broker import broker
# from app.services.groq_bot import build_reply
# from app.services.messenger_send import send_text_message

# router = APIRouter(prefix="/webhook", tags=["messenger"])

# def verify_signature(app_secret: str, signature: str, body: bytes) -> bool:
#     """
#     Meta sends: X-Hub-Signature-256: sha256=<hash>
#     We compute HMAC SHA256 of request body using app secret and compare.
#     """
#     if not signature or not signature.startswith("sha256="):
#         return False
#     sig_hash = signature.split("=", 1)[1]
#     mac = hmac.new(app_secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
#     expected = mac.hexdigest()
#     return hmac.compare_digest(expected, sig_hash)

# @router.get("")
# async def webhook_verify(request: Request):
#     """
#     Meta verification:
#     GET /webhook?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...
#     """
#     params = request.query_params
#     mode = params.get("hub.mode")
#     token = params.get("hub.verify_token")
#     challenge = params.get("hub.challenge")

#     if mode == "subscribe" and token == settings.FB_VERIFY_TOKEN:
#         return int(challenge)
#     raise HTTPException(status_code=403, detail="Verification failed")

# @router.post("")
# async def webhook_receive(request: Request, db: Session = Depends(get_db)):
#     raw_body = await request.body()

#     # debug
#     print("Webhook POST received")
#     print("Headers:", dict(request.headers))
#     print("Raw body:", raw_body.decode("utf-8")[:500])

#     # Signature validation (important for security)
#     sig = request.headers.get("x-hub-signature-256", "")
#     if settings.FB_APP_SECRET:
#         if not verify_signature(settings.FB_APP_SECRET, sig, raw_body):
#             raise HTTPException(status_code=403, detail="Invalid signature")

#     payload: Dict[str, Any] = json.loads(raw_body.decode("utf-8"))

#     # Messenger payload structure: entry -> messaging[]
#     if payload.get("object") != "page":
#         return {"ok": True}

#     for entry in payload.get("entry", []):
#         for event in entry.get("messaging", []):
#             sender = event.get("sender", {}).get("id")  # PSID
#             message = event.get("message", {})
#             text = message.get("text")
#             mid = message.get("mid")

#             # Ignore echoes (messages sent by Page itself), to avoid infinite loops
#             if message.get("is_echo"):
#                 continue

#             # ignore non-text for MVP
#             if not sender or not text:
#                 continue

#             # Check for duplicate message delivery
#             if mid:
#                 existing = db.execute(
#                     select(Message).where(Message.platform_message_id == mid)
#                 ).scalar_one_or_none()
#                 if existing:
#                     # Duplicate delivery from Meta, ignore
#                     continue

#             # 1) find/create customer
#             customer = db.execute(select(Customer).where(Customer.psid == sender)).scalar_one_or_none()
#             if not customer:
#                 customer = Customer(psid=sender)
#                 db.add(customer)
#                 db.commit()
#                 db.refresh(customer)

#             # 2) find/create conversation (1 customer = 1 conv)
#             conv = db.execute(select(Conversation).where(Conversation.customer_id == customer.id)).scalar_one_or_none()
#             if not conv:
#                 conv = Conversation(customer_id=customer.id, status="BOT_ACTIVE")
#                 db.add(conv)
#                 db.commit()
#                 db.refresh(conv)

#             # 3) save inbound message
#             msg = Message(
#                 conversation_id=conv.id,
#                 direction="inbound",
#                 sender_type="customer",
#                 content=text,
#                 platform_message_id=mid
#             )
#             db.add(msg)
#             db.commit()
#             db.refresh(msg)

#             # 4) publish realtime event (Agent dashboard live update)
#             await broker.publish(conv.id, {
#                 "id": msg.id,
#                 "direction": msg.direction,
#                 "sender_type": msg.sender_type,
#                 "content": msg.content,
#                 "created_at": msg.created_at.isoformat() if msg.created_at else None
#             })

#             # 5) Enqueue bot job (do not call LLM inside webhook)
#             try:
#                 job = BotJob(conversation_id=conv.id, inbound_message_id=msg.id, status="queued")
#                 db.add(job)
#                 db.commit()
#             except Exception as e:
#                 # If job already exists (unique), ignore
#                 db.rollback()
#                 print(f"[Job enqueue] {e}")


#     return {"ok": True}


# edit 4


import hmac
import hashlib
import json
from typing import Any, Dict

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy import text as sql_text

from app.core.config import settings
from app.db.session import get_db
from app.db.models import Customer, Conversation, Message, BotJob
from app.realtime.broker import broker
from app.services.groq_bot import build_reply
from app.services.messenger_send import send_text_message


from app.services.fb_profile import fetch_fb_name
# from sqlalchemy import text

router = APIRouter(prefix="/webhook", tags=["messenger"])

def verify_signature(app_secret: str, signature: str, body: bytes) -> bool:
    """
    Meta sends: X-Hub-Signature-256: sha256=<hash>
    We compute HMAC SHA256 of request body using app secret and compare.
    """
    if not signature or not signature.startswith("sha256="):
        return False
    sig_hash = signature.split("=", 1)[1]
    mac = hmac.new(app_secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
    expected = mac.hexdigest()
    return hmac.compare_digest(expected, sig_hash)

@router.get("")
async def webhook_verify(request: Request):
    """
    Meta verification:
    GET /webhook?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.FB_VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("")
async def webhook_receive(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()

    # debug
    print("Webhook POST received")
    print("Headers:", dict(request.headers))
    print("Raw body:", raw_body.decode("utf-8")[:500])

    # Signature validation (important for security)
    sig = request.headers.get("x-hub-signature-256", "")
    if settings.FB_APP_SECRET:
        if not verify_signature(settings.FB_APP_SECRET, sig, raw_body):
            raise HTTPException(status_code=403, detail="Invalid signature")

    payload: Dict[str, Any] = json.loads(raw_body.decode("utf-8"))

    # Messenger payload structure: entry -> messaging[]
    if payload.get("object") != "page":
        return {"ok": True}

    for entry in payload.get("entry", []):
        for event in entry.get("messaging", []):
            sender = event.get("sender", {}).get("id")  # PSID
            message = event.get("message", {})
            text = message.get("text")
            mid = message.get("mid")

            # Ignore echoes (messages sent by Page itself), to avoid infinite loops
            if message.get("is_echo"):
                continue

            # ignore non-text for MVP
            if not sender or not text:
                continue

            # Check for duplicate message delivery
            if mid:
                existing = db.execute(
                    select(Message).where(Message.platform_message_id == mid)
                ).scalar_one_or_none()
                if existing:
                    # Duplicate delivery from Meta, ignore
                    continue

            # 1) find/create customer
            customer = db.execute(select(Customer).where(Customer.psid == sender)).scalar_one_or_none()
            if not customer:
                customer = Customer(psid=sender)
                name = fetch_fb_name(sender)
                if name:
                    customer.fb_name = name
                db.add(customer)
                db.commit()
                db.refresh(customer)
            
            else:
                # Existing customer: fetch name only once if missing
                if not customer.fb_name:
                    name = fetch_fb_name(sender)
                    if name:
                        db.execute(
                            # text("update customers set fb_name=:n where id=:id"),
                            sql_text("update customers set fb_name=:n where id=:id"),
                            {"n": name, "id": customer.id},
                        )
                        db.commit()
                        customer.fb_name = name

            # 2) find/create conversation (1 customer = 1 conv)
            conv = db.execute(select(Conversation).where(Conversation.customer_id == customer.id)).scalar_one_or_none()
            if not conv:
                conv = Conversation(customer_id=customer.id, status="BOT_ACTIVE")
                db.add(conv)
                db.commit()
                db.refresh(conv)

            # 3) save inbound message
            msg = Message(
                conversation_id=conv.id,
                direction="inbound",
                sender_type="customer",
                content=text,
                platform_message_id=mid
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)

            # 4) publish realtime event (Agent dashboard live update)
            await broker.publish(conv.id, {
                "id": msg.id,
                "direction": msg.direction,
                "sender_type": msg.sender_type,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            })

            # 5) Enqueue bot job (do not call LLM inside webhook)
            try:
                job = BotJob(conversation_id=conv.id, inbound_message_id=msg.id, status="queued")
                db.add(job)
                db.commit()
            except Exception as e:
                # If job already exists (unique), ignore
                db.rollback()
                print(f"[Job enqueue] {e}")


    return {"ok": True}