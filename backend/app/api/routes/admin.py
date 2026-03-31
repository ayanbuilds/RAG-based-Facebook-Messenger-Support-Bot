# from fastapi import APIRouter, Depends, HTTPException, Request
# from sqlalchemy.orm import Session
# from sqlalchemy import select, text

# from app.db.session import get_db
# from app.db.models import Conversation, Customer, Message
# from app.services.messenger_send import send_text_message

# from app.core.supabase_auth import require_supabase_user


# router = APIRouter(prefix="/api/admin", tags=["admin"])

# @router.post("/conversations/{conversation_id}/status")
# def set_status(conversation_id: int, status: str, db: Session = Depends(get_db)):
#     if status not in ("BOT_ACTIVE", "NEEDS_HUMAN", "RESOLVED"):
#         raise HTTPException(status_code=400, detail="Invalid status")

#     conv = db.get(Conversation, conversation_id)
#     if not conv:
#         raise HTTPException(status_code=404, detail="Conversation not found")

#     db.execute(
#         text("update conversations set status=:s, updated_at=now() where id=:id"),
#         {"s": status, "id": conversation_id},
#     )
#     db.commit()
#     return {"ok": True, "status": status}

# @router.post("/conversations/{conversation_id}/reply")
# def admin_reply(conversation_id: int, content: str, db: Session = Depends(get_db)):
#     conv = db.get(Conversation, conversation_id)
#     if not conv:
#         raise HTTPException(status_code=404, detail="Conversation not found")

#     customer = db.execute(
#         select(Customer).where(Customer.id == conv.customer_id)
#     ).scalar_one_or_none()
#     if not customer:
#         raise HTTPException(status_code=404, detail="Customer not found")

#     msg = Message(
#         conversation_id=conversation_id,
#         direction="outbound",
#         sender_type="admin",
#         content=content,
#         platform_message_id=None,
#     )
#     db.add(msg)
#     db.commit()
#     db.refresh(msg)

#     send_text_message(customer.psid, content)

#     return {"ok": True, "message_id": msg.id}


# edit 2

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, text

from app.db.session import get_db
from app.db.models import Conversation, Customer, Message
from app.services.messenger_send import send_text_message

from app.core.supabase_auth import require_supabase_user


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/conversations/{conversation_id}/status")
def set_status(conversation_id: int, status: str, request: Request, db: Session = Depends(get_db), user=Depends(require_supabase_user)):
    if status not in ("BOT_ACTIVE", "NEEDS_HUMAN", "RESOLVED"):
        raise HTTPException(status_code=400, detail="Invalid status")

    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.execute(
        text("update conversations set status=:s, updated_at=now() where id=:id"),
        {"s": status, "id": conversation_id},
    )
    db.commit()
    return {"ok": True, "status": status}

@router.post("/conversations/{conversation_id}/reply")
def admin_reply(conversation_id: int, content: str, request: Request, db: Session = Depends(get_db), user=Depends(require_supabase_user)):
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    customer = db.execute(
        select(Customer).where(Customer.id == conv.customer_id)
    ).scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    msg = Message(
        conversation_id=conversation_id,
        direction="outbound",
        sender_type="admin",
        content=content,
        platform_message_id=None,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    send_text_message(customer.psid, content)

    return {"ok": True, "message_id": msg.id}