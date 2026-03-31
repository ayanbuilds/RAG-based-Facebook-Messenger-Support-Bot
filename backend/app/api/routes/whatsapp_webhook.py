# import hmac
# import hashlib
# from typing import Any, Dict, Optional

# from fastapi import APIRouter, Request, HTTPException, Depends
# from sqlalchemy.orm import Session
# from sqlalchemy import select

# from app.core.config import settings
# from app.db.session import get_db
# from app.db.models import Customer, Conversation, Message, BotJob

# router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])


# def verify_signature(app_secret: str, signature: str, body: bytes) -> bool:
#     """
#     Meta sends: X-Hub-Signature-256: sha256=<hash>
#     Validate HMAC SHA256 of request body using Meta App Secret.
#     """
#     if not signature or not signature.startswith("sha256="):
#         return False
#     sig_hash = signature.split("=", 1)[1]
#     mac = hmac.new(app_secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
#     expected = mac.hexdigest()
#     return hmac.compare_digest(expected, sig_hash)


# @router.get("")
# async def whatsapp_verify(request: Request):
#     """
#     Webhook verification:
#     GET ?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...
#     """
#     params = request.query_params
#     mode = params.get("hub.mode")
#     token = params.get("hub.verify_token")
#     challenge = params.get("hub.challenge")

#     if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
#         return int(challenge)

#     raise HTTPException(status_code=403, detail="Verification failed")


# def _extract_text_message(payload: Dict[str, Any]) -> Optional[Dict[str, str]]:
#     """
#     WhatsApp webhook payload shape (Cloud API):
#     entry[].changes[].value.messages[] contains inbound messages.

#     Returns:
#       {
#         "wa_id": "<sender wa_id>",
#         "text": "<message text>",
#         "mid": "<message id (wamid...)>"
#       }
#     or None if not a text message.
#     """
#     try:
#         entries = payload.get("entry", [])
#         for entry in entries:
#             changes = entry.get("changes", [])
#             for change in changes:
#                 value = change.get("value", {})
#                 messages = value.get("messages", [])
#                 for m in messages:
#                     # Only text messages for MVP
#                     if m.get("type") != "text":
#                         continue
#                     wa_id = m.get("from")
#                     text = (m.get("text") or {}).get("body")
#                     mid = m.get("id")  # wamid...
#                     if wa_id and text and mid:
#                         return {"wa_id": wa_id, "text": text, "mid": mid}
#     except Exception:
#         return None
#     return None


# @router.post("")
# async def whatsapp_receive(request: Request, db: Session = Depends(get_db)):
#     raw_body = await request.body()

#     # Optional signature verification (recommended)
#     # app_secret = settings.WHATSAPP_APP_SECRET or getattr(settings, "FB_APP_SECRET", "") or ""
#     # sig = request.headers.get("x-hub-signature-256", "")
#     # if app_secret:
#     #     if not verify_signature(app_secret, sig, raw_body):
#     #         raise HTTPException(status_code=403, detail="Invalid signature")

#     try:
#         payload: Dict[str, Any] = await request.json()
#     except Exception:
#         # Always return OK so Meta doesn't retry forever on malformed JSON
#         return {"ok": True}

#     # We only process "messages" events
#     extracted = _extract_text_message(payload)
#     if not extracted:
#         return {"ok": True}

#     wa_id = extracted["wa_id"]
#     text = extracted["text"]
#     mid = extracted["mid"]

#     # Idempotency: ignore duplicate deliveries
#     existing = db.execute(
#         select(Message).where(Message.platform_message_id == mid)
#     ).scalar_one_or_none()
#     if existing:
#         return {"ok": True}

#     # 1) find/create customer (platform=whatsapp)
#     customer = db.execute(
#         select(Customer).where(Customer.platform == "whatsapp", Customer.psid == wa_id)
#     ).scalar_one_or_none()

#     if not customer:
#         customer = Customer(platform="whatsapp", psid=wa_id)
#         db.add(customer)
#         db.commit()
#         db.refresh(customer)

#     # 2) find/create conversation (1 customer = 1 conversation)
#     conv = db.execute(
#         select(Conversation).where(Conversation.customer_id == customer.id)
#     ).scalar_one_or_none()

#     if not conv:
#         conv = Conversation(customer_id=customer.id, status="BOT_ACTIVE")
#         db.add(conv)
#         db.commit()
#         db.refresh(conv)

#     # 3) save inbound message
#     msg = Message(
#         conversation_id=conv.id,
#         direction="inbound",
#         sender_type="customer",
#         content=text,
#         platform_message_id=mid,
#     )
#     db.add(msg)
#     db.commit()
#     db.refresh(msg)

#     # 4) enqueue bot job (LLM handled in worker, not here)
#     try:
#         job = BotJob(conversation_id=conv.id, inbound_message_id=msg.id, status="queued")
#         db.add(job)
#         db.commit()
#     except Exception:
#         db.rollback()

#     return {"ok": True}

# ------------------------------------------------------------------------------------------------------------------------------------------------------------

# import hmac
# import hashlib
# import logging
# from typing import Any, Dict, Optional

# from fastapi import APIRouter, Request, HTTPException, Depends
# from sqlalchemy.orm import Session
# from sqlalchemy import select

# from app.core.config import settings
# from app.db.session import get_db
# from app.db.models import Customer, Conversation, Message, BotJob

# # Set up logging
# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])


# def verify_signature(app_secret: str, signature: str, body: bytes) -> bool:
#     """
#     Meta sends: X-Hub-Signature-256: sha256=<hash>
#     Validate HMAC SHA256 of request body using Meta App Secret.
#     """
#     if not signature or not signature.startswith("sha256="):
#         return False
    
#     try:
#         sig_hash = signature.split("=", 1)[1]
#         mac = hmac.new(app_secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
#         expected = mac.hexdigest()
#         return hmac.compare_digest(expected, sig_hash)
#     except Exception as e:
#         logger.error(f"Error verifying signature: {e}")
#         return False


# @router.get("")
# async def whatsapp_verify(request: Request):
#     """
#     Webhook verification:
#     GET ?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...
#     """
#     params = request.query_params
#     mode = params.get("hub.mode")
#     token = params.get("hub.verify_token")
#     challenge = params.get("hub.challenge")

#     logger.info(f"Webhook verification attempt - mode: {mode}, token_match: {token == settings.WHATSAPP_VERIFY_TOKEN}")

#     if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
#         logger.info("Webhook verification successful")
#         return int(challenge)

#     logger.warning("Webhook verification failed")
#     raise HTTPException(status_code=403, detail="Verification failed")


# def _extract_text_message(payload: Dict[str, Any]) -> Optional[Dict[str, str]]:
#     """
#     WhatsApp webhook payload shape (Cloud API):
#     entry[].changes[].value.messages[] contains inbound messages.

#     Returns:
#       {
#         "wa_id": "<sender wa_id>",
#         "text": "<message text>",
#         "mid": "<message id (wamid...)>"
#       }
#     or None if not a text message.
#     """
#     try:
#         entries = payload.get("entry", [])
#         for entry in entries:
#             changes = entry.get("changes", [])
#             for change in changes:
#                 value = change.get("value", {})
#                 messages = value.get("messages", [])
#                 for m in messages:
#                     # Only text messages for MVP
#                     if m.get("type") != "text":
#                         logger.info(f"Skipping non-text message type: {m.get('type')}")
#                         continue
                    
#                     wa_id = m.get("from")
#                     text = (m.get("text") or {}).get("body")
#                     mid = m.get("id")  # wamid...
                    
#                     if wa_id and text and mid:
#                         logger.info(f"Extracted message - wa_id: {wa_id}, mid: {mid}")
#                         return {"wa_id": wa_id, "text": text, "mid": mid}
#     except Exception as e:
#         logger.error(f"Error extracting text message: {e}", exc_info=True)
#         return None
    
#     return None


# @router.post("")
# async def whatsapp_receive(request: Request, db: Session = Depends(get_db)):
#     """
#     Handle incoming WhatsApp messages from Meta Cloud API.
#     """
#     # Log incoming request
#     logger.info(f"Webhook received - Headers: {dict(request.headers)}")
    
#     raw_body = await request.body()
#     logger.info(f"Raw body length: {len(raw_body)} bytes")

#     # Signature verification (only if app secret is configured)
#     app_secret = getattr(settings, "WHATSAPP_APP_SECRET", None) or getattr(settings, "FB_APP_SECRET", None)
#     sig = request.headers.get("x-hub-signature-256", "")
    
#     # Only verify signature if app_secret is configured
#     if app_secret:
#         if sig:
#             # Signature present, verify it
#             if not verify_signature(app_secret, sig, raw_body):
#                 logger.error("Signature verification failed")
#                 raise HTTPException(status_code=403, detail="Invalid signature")
#             logger.info("Signature verification successful")
#         else:
#             # In production, you might want to reject requests without signature
#             # For now, we'll allow it for testing purposes
#             logger.warning("No signature provided, but app_secret is configured. Allowing for testing.")
#     else:
#         logger.info("No app_secret configured, skipping signature verification")

#     # Parse JSON payload
#     try:
#         payload: Dict[str, Any] = await request.json()
#         logger.info(f"Parsed payload: {payload}")
#     except Exception as e:
#         logger.error(f"Error parsing JSON: {e}", exc_info=True)
#         # Always return OK so Meta doesn't retry forever on malformed JSON
#         return {"ok": True}

#     # We only process "messages" events
#     extracted = _extract_text_message(payload)
#     if not extracted:
#         logger.info("No text message found in payload")
#         return {"ok": True}

#     wa_id = extracted["wa_id"]
#     text = extracted["text"]
#     mid = extracted["mid"]

#     logger.info(f"Processing message - wa_id: {wa_id}, text: {text[:50]}..., mid: {mid}")

#     try:
#         # Idempotency: ignore duplicate deliveries
#         existing = db.execute(
#             select(Message).where(Message.platform_message_id == mid)
#         ).scalar_one_or_none()
        
#         if existing:
#             logger.info(f"Duplicate message ignored - mid: {mid}")
#             return {"ok": True}

#         # 1) Find/create customer (platform=whatsapp)
#         customer = db.execute(
#             select(Customer).where(
#                 Customer.platform == "whatsapp",
#                 Customer.psid == wa_id
#             )
#         ).scalar_one_or_none()

#         if not customer:
#             logger.info(f"Creating new customer - wa_id: {wa_id}")
#             customer = Customer(platform="whatsapp", psid=wa_id)
#             db.add(customer)
#             db.commit()
#             db.refresh(customer)
#             logger.info(f"Customer created - id: {customer.id}")
#         else:
#             logger.info(f"Found existing customer - id: {customer.id}")

#         # 2) Find/create conversation (1 customer = 1 conversation)
#         conv = db.execute(
#             select(Conversation).where(Conversation.customer_id == customer.id)
#         ).scalar_one_or_none()

#         if not conv:
#             logger.info(f"Creating new conversation for customer_id: {customer.id}")
#             conv = Conversation(customer_id=customer.id, status="BOT_ACTIVE")
#             db.add(conv)
#             db.commit()
#             db.refresh(conv)
#             logger.info(f"Conversation created - id: {conv.id}")
#         else:
#             logger.info(f"Found existing conversation - id: {conv.id}")

#         # 3) Save inbound message
#         msg = Message(
#             conversation_id=conv.id,
#             direction="inbound",
#             sender_type="customer",
#             content=text,
#             platform_message_id=mid,
#         )
#         db.add(msg)
#         db.commit()
#         db.refresh(msg)
#         logger.info(f"Message saved - id: {msg.id}")

#         # 4) Enqueue bot job (LLM handled in worker, not here)
#         try:
#             job = BotJob(
#                 conversation_id=conv.id,
#                 inbound_message_id=msg.id,
#                 status="queued"
#             )
#             db.add(job)
#             db.commit()
#             logger.info(f"Bot job created - id: {job.id}")
#         except Exception as e:
#             logger.error(f"Error creating bot job: {e}", exc_info=True)
#             db.rollback()
#             # Continue anyway - message is saved

#         logger.info(f"Message processing complete - mid: {mid}")
#         return {"ok": True}

#     except Exception as e:
#         logger.error(f"Error processing webhook: {e}", exc_info=True)
#         db.rollback()
#         # Always return OK to prevent Meta from retrying
#         return {"ok": True}

# -----------------------------------------------------------------------------------------------------

# import hmac
# import hashlib
# import logging
# from typing import Any, Dict, Optional
# from datetime import datetime

# from fastapi import APIRouter, Request, HTTPException, Depends
# from sqlalchemy.orm import Session
# from sqlalchemy import select

# from app.core.config import settings
# from app.db.session import get_db
# from app.db.models import Customer, Conversation, Message, BotJob

# # Set up logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])


# def verify_signature(app_secret: str, signature: str, body: bytes) -> bool:
#     """
#     Meta sends: X-Hub-Signature-256: sha256=<hash>
#     Validate HMAC SHA256 of request body using Meta App Secret.
#     """
#     if not signature or not signature.startswith("sha256="):
#         return False
    
#     try:
#         sig_hash = signature.split("=", 1)[1]
#         mac = hmac.new(app_secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
#         expected = mac.hexdigest()
#         return hmac.compare_digest(expected, sig_hash)
#     except Exception as e:
#         logger.error(f"Error verifying signature: {e}")
#         return False


# @router.get("")
# async def whatsapp_verify(request: Request):
#     """
#     Webhook verification endpoint for Meta
#     """
#     params = request.query_params
#     mode = params.get("hub.mode")
#     token = params.get("hub.verify_token")
#     challenge = params.get("hub.challenge")

#     logger.info("=" * 80)
#     logger.info("WEBHOOK VERIFICATION REQUEST")
#     logger.info(f"Mode: {mode}")
#     logger.info(f"Token received: {token}")
#     logger.info(f"Token expected: {settings.WHATSAPP_VERIFY_TOKEN}")
#     logger.info(f"Challenge: {challenge}")
#     logger.info("=" * 80)

#     if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
#         logger.info("✅ VERIFICATION SUCCESSFUL")
#         return int(challenge)

#     logger.error("❌ VERIFICATION FAILED")
#     raise HTTPException(status_code=403, detail="Verification failed")


# def _extract_text_message(payload: Dict[str, Any]) -> Optional[Dict[str, str]]:
#     """
#     Extract text message from WhatsApp webhook payload
#     """
#     try:
#         entries = payload.get("entry", [])
#         logger.info(f"Number of entries: {len(entries)}")
        
#         for entry in entries:
#             changes = entry.get("changes", [])
#             logger.info(f"Number of changes: {len(changes)}")
            
#             for change in changes:
#                 value = change.get("value", {})
#                 messages = value.get("messages", [])
#                 logger.info(f"Number of messages: {len(messages)}")
                
#                 for m in messages:
#                     msg_type = m.get("type")
#                     logger.info(f"Message type: {msg_type}")
                    
#                     # Only text messages for MVP
#                     if msg_type != "text":
#                         logger.info(f"Skipping non-text message type: {msg_type}")
#                         continue
                    
#                     wa_id = m.get("from")
#                     text = (m.get("text") or {}).get("body")
#                     mid = m.get("id")
                    
#                     logger.info(f"Extracted - wa_id: {wa_id}, text: '{text}', mid: {mid}")
                    
#                     if wa_id and text and mid:
#                         return {"wa_id": wa_id, "text": text, "mid": mid}
                        
#     except Exception as e:
#         logger.error(f"Error extracting text message: {e}", exc_info=True)
#         return None
    
#     return None


# @router.post("")
# async def whatsapp_receive(request: Request, db: Session = Depends(get_db)):
#     """
#     Handle incoming WhatsApp webhook events
#     """
#     timestamp = datetime.now().isoformat()
    
#     logger.info("=" * 80)
#     logger.info(f"🔔 WEBHOOK POST REQUEST RECEIVED at {timestamp}")
#     logger.info("=" * 80)
    
#     # Log all headers
#     logger.info("REQUEST HEADERS:")
#     for key, value in request.headers.items():
#         logger.info(f"  {key}: {value}")
    
#     raw_body = await request.body()
#     logger.info(f"Raw body length: {len(raw_body)} bytes")
#     logger.info(f"Raw body preview: {raw_body[:500]}")

#     # Signature verification
#     app_secret = getattr(settings, "WHATSAPP_APP_SECRET", None) or getattr(settings, "FB_APP_SECRET", None)
#     sig = request.headers.get("x-hub-signature-256", "")
    
#     if app_secret:
#         logger.info(f"App secret configured: Yes (length: {len(app_secret)})")
#         if sig:
#             logger.info(f"Signature present: {sig[:20]}...")
#             if not verify_signature(app_secret, sig, raw_body):
#                 logger.error("❌ Signature verification FAILED")
#                 raise HTTPException(status_code=403, detail="Invalid signature")
#             logger.info("✅ Signature verification SUCCESS")
#         else:
#             logger.warning("⚠️ No signature in request (allowing for testing)")
#     else:
#         logger.info("App secret not configured, skipping verification")

#     # Parse JSON
#     try:
#         payload: Dict[str, Any] = await request.json()
#         logger.info("PARSED PAYLOAD:")
#         logger.info(f"{payload}")
#     except Exception as e:
#         logger.error(f"❌ JSON parsing error: {e}", exc_info=True)
#         return {"ok": True}

#     # Extract message
#     extracted = _extract_text_message(payload)
#     if not extracted:
#         logger.warning("⚠️ No text message extracted from payload")
#         logger.info("Payload object keys: " + str(payload.get("object")))
#         logger.info("Entry count: " + str(len(payload.get("entry", []))))
#         return {"ok": True}

#     wa_id = extracted["wa_id"]
#     text = extracted["text"]
#     mid = extracted["mid"]

#     logger.info(f"📱 MESSAGE EXTRACTED:")
#     logger.info(f"  From: {wa_id}")
#     logger.info(f"  Text: {text}")
#     logger.info(f"  Message ID: {mid}")

#     try:
#         # Check for duplicates
#         existing = db.execute(
#             select(Message).where(Message.platform_message_id == mid)
#         ).scalar_one_or_none()
        
#         if existing:
#             logger.info(f"⚠️ Duplicate message ignored: {mid}")
#             return {"ok": True}

#         # Find/create customer
#         customer = db.execute(
#             select(Customer).where(
#                 Customer.platform == "whatsapp",
#                 Customer.psid == wa_id
#             )
#         ).scalar_one_or_none()

#         if not customer:
#             logger.info(f"Creating new customer for wa_id: {wa_id}")
#             customer = Customer(platform="whatsapp", psid=wa_id)
#             db.add(customer)
#             db.commit()
#             db.refresh(customer)
#             logger.info(f"✅ Customer created: ID={customer.id}")
#         else:
#             logger.info(f"✅ Found existing customer: ID={customer.id}")

#         # Find/create conversation
#         conv = db.execute(
#             select(Conversation).where(Conversation.customer_id == customer.id)
#         ).scalar_one_or_none()

#         if not conv:
#             logger.info(f"Creating new conversation for customer: {customer.id}")
#             conv = Conversation(customer_id=customer.id, status="BOT_ACTIVE")
#             db.add(conv)
#             db.commit()
#             db.refresh(conv)
#             logger.info(f"✅ Conversation created: ID={conv.id}")
#         else:
#             logger.info(f"✅ Found existing conversation: ID={conv.id}")

#         # Save message
#         msg = Message(
#             conversation_id=conv.id,
#             direction="inbound",
#             sender_type="customer",
#             content=text,
#             platform_message_id=mid,
#         )
#         db.add(msg)
#         db.commit()
#         db.refresh(msg)
#         logger.info(f"✅ Message saved: ID={msg.id}")

#         # Create bot job
#         try:
#             job = BotJob(
#                 conversation_id=conv.id,
#                 inbound_message_id=msg.id,
#                 status="queued"
#             )
#             db.add(job)
#             db.commit()
#             logger.info(f"✅ Bot job created: ID={job.id}")
#         except Exception as e:
#             logger.error(f"❌ Error creating bot job: {e}", exc_info=True)
#             db.rollback()

#         logger.info("=" * 80)
#         logger.info("✅ MESSAGE PROCESSING COMPLETE")
#         logger.info("=" * 80)
        
#         return {"ok": True}

#     except Exception as e:
#         logger.error(f"❌ Error processing webhook: {e}", exc_info=True)
#         db.rollback()
#         return {"ok": True}

import hmac
import hashlib
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.db.session import get_db
from app.db.models import Customer, Conversation, Message, BotJob

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])


def verify_signature(app_secret: str, signature: str, body: bytes) -> bool:
    """
    Meta sends: X-Hub-Signature-256: sha256=<hash>
    Validate HMAC SHA256 of request body using Meta App Secret.
    """
    if not signature or not signature.startswith("sha256="):
        return False
    
    try:
        sig_hash = signature.split("=", 1)[1]
        mac = hmac.new(app_secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
        expected = mac.hexdigest()
        return hmac.compare_digest(expected, sig_hash)
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False


@router.get("")
async def whatsapp_verify(request: Request):
    """
    Webhook verification endpoint for Meta
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    logger.info("=" * 80)
    logger.info("WEBHOOK VERIFICATION REQUEST")
    logger.info(f"Mode: {mode}")
    logger.info(f"Token match: {token == settings.WHATSAPP_VERIFY_TOKEN}")
    logger.info(f"Challenge: {challenge}")
    logger.info("=" * 80)

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("✅ VERIFICATION SUCCESSFUL")
        return int(challenge)

    logger.error("❌ VERIFICATION FAILED")
    raise HTTPException(status_code=403, detail="Verification failed")


def _extract_text_message(payload: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Extract text message from WhatsApp webhook payload.
    Handles both formats:
    1. Test format: {"field": "messages", "value": {"messages": [...]}}
    2. Production format: {"entry": [{"changes": [{"value": {"messages": [...]}}]}]}
    """
    try:
        messages_list = []
        
        # Format 1: Direct test payload from Meta Console
        if "field" in payload and payload.get("field") == "messages":
            logger.info("Detected TEST payload format")
            value = payload.get("value", {})
            messages_list = value.get("messages", [])
        
        # Format 2: Production webhook format with entry/changes
        elif "entry" in payload:
            logger.info("Detected PRODUCTION payload format")
            entries = payload.get("entry", [])
            logger.info(f"Number of entries: {len(entries)}")
            
            for entry in entries:
                changes = entry.get("changes", [])
                logger.info(f"Number of changes: {len(changes)}")
                
                for change in changes:
                    value = change.get("value", {})
                    messages_list.extend(value.get("messages", []))
        
        else:
            logger.warning("Unknown payload format")
            logger.info(f"Payload keys: {list(payload.keys())}")
            return None
        
        logger.info(f"Total messages found: {len(messages_list)}")
        
        # Process messages
        for m in messages_list:
            msg_type = m.get("type")
            logger.info(f"Message type: {msg_type}")
            
            # Only text messages for MVP
            if msg_type != "text":
                logger.info(f"Skipping non-text message type: {msg_type}")
                continue
            
            wa_id = m.get("from")
            text = (m.get("text") or {}).get("body")
            mid = m.get("id")
            
            logger.info(f"Extracted - wa_id: {wa_id}, text: '{text}', mid: {mid}")
            
            if wa_id and text and mid:
                return {"wa_id": wa_id, "text": text, "mid": mid}
                        
    except Exception as e:
        logger.error(f"Error extracting text message: {e}", exc_info=True)
        return None
    
    return None


@router.post("")
async def whatsapp_receive(request: Request, db: Session = Depends(get_db)):
    """
    Handle incoming WhatsApp webhook events
    """
    timestamp = datetime.now().isoformat()
    
    logger.info("=" * 80)
    logger.info(f"🔔 WEBHOOK POST REQUEST RECEIVED at {timestamp}")
    logger.info("=" * 80)
    
    # Log all headers
    logger.info("REQUEST HEADERS:")
    for key, value in request.headers.items():
        logger.info(f"  {key}: {value}")
    
    raw_body = await request.body()
    logger.info(f"Raw body length: {len(raw_body)} bytes")
    if not raw_body:
        logger.warning("Empty request body; nothing to process")
        return {"ok": True}
    
    # Signature verification (optional for testing)
    app_secret = getattr(settings, "WHATSAPP_APP_SECRET", None) or getattr(settings, "FB_APP_SECRET", None)
    sig = request.headers.get("x-hub-signature-256", "")
    
    if app_secret and sig:
        logger.info("Verifying signature...")
        if not verify_signature(app_secret, sig, raw_body):
            logger.error("❌ Signature verification FAILED")
            raise HTTPException(status_code=403, detail="Invalid signature")
        logger.info("✅ Signature verification SUCCESS")
    else:
        logger.info("⚠️ Skipping signature verification (testing mode)")

    # Parse JSON
    try:
        payload: Dict[str, Any] = await request.json()
        logger.info("PARSED PAYLOAD:")
        logger.info(f"{payload}")
    except Exception as e:
        logger.error(f"❌ JSON parsing error: {e}", exc_info=True)
        return {"ok": True}

    # Extract message
    extracted = _extract_text_message(payload)
    if not extracted:
        logger.warning("⚠️ No text message extracted from payload")
        
        # Log diagnostic info
        if "object" in payload:
            logger.info(f"Payload object: {payload.get('object')}")
        if "entry" in payload:
            logger.info(f"Entry count: {len(payload.get('entry', []))}")
        if "field" in payload:
            logger.info(f"Field: {payload.get('field')}")
            
        return {"ok": True}

    wa_id = extracted["wa_id"]
    text = extracted["text"]
    mid = extracted["mid"]

    logger.info(f"📱 MESSAGE EXTRACTED:")
    logger.info(f"  From: {wa_id}")
    logger.info(f"  Text: {text}")
    logger.info(f"  Message ID: {mid}")

    try:
        # Check for duplicates
        existing = db.execute(
            select(Message).where(Message.platform_message_id == mid)
        ).scalar_one_or_none()
        
        if existing:
            logger.info(f"⚠️ Duplicate message ignored: {mid}")
            return {"ok": True}

        # Find/create customer
        customer = db.execute(
            select(Customer).where(
                Customer.platform == "whatsapp",
                Customer.psid == wa_id
            )
        ).scalar_one_or_none()

        if not customer:
            logger.info(f"Creating new customer for wa_id: {wa_id}")
            customer = Customer(platform="whatsapp", psid=wa_id)
            db.add(customer)
            db.commit()
            db.refresh(customer)
            logger.info(f"✅ Customer created: ID={customer.id}")
        else:
            logger.info(f"✅ Found existing customer: ID={customer.id}")

        # Find/create conversation
        conv = db.execute(
            select(Conversation).where(Conversation.customer_id == customer.id)
        ).scalar_one_or_none()

        if not conv:
            logger.info(f"Creating new conversation for customer: {customer.id}")
            conv = Conversation(customer_id=customer.id, status="BOT_ACTIVE")
            db.add(conv)
            db.commit()
            db.refresh(conv)
            logger.info(f"✅ Conversation created: ID={conv.id}")
        else:
            logger.info(f"✅ Found existing conversation: ID={conv.id}")

        # Save message
        msg = Message(
            conversation_id=conv.id,
            direction="inbound",
            sender_type="customer",
            content=text,
            platform_message_id=mid,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        logger.info(f"✅ Message saved: ID={msg.id}")

        # Create bot job
        try:
            job = BotJob(
                conversation_id=conv.id,
                inbound_message_id=msg.id,
                status="queued"
            )
            db.add(job)
            db.commit()
            logger.info(f"✅ Bot job created: ID={job.id}")
        except Exception as e:
            logger.error(f"❌ Error creating bot job: {e}", exc_info=True)
            db.rollback()

        logger.info("=" * 80)
        logger.info("✅ MESSAGE PROCESSING COMPLETE")
        logger.info("=" * 80)
        
        return {"ok": True}

    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}", exc_info=True)
        db.rollback()
        return {"ok": True}
