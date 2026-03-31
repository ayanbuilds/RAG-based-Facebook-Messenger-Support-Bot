# import json
# from fastapi import APIRouter, Depends, HTTPException
# from fastapi.responses import StreamingResponse
# from sqlalchemy.orm import Session
# from sqlalchemy import select

# from app.db.session import get_db
# from app.db.models import Conversation, Message, Customer
# from app.realtime.broker import broker

# router = APIRouter(prefix="/api", tags=["chat"])

# @router.get("/conversations")
# def list_conversations(db: Session = Depends(get_db)):
#     rows = db.execute(select(Conversation).order_by(Conversation.updated_at.desc())).scalars().all()
#     return [
#         {
#             "id": c.id,
#             "customer_id": c.customer_id,
#             "status": c.status,
#             "updated_at": c.updated_at.isoformat() if c.updated_at else None
#         }
#         for c in rows
#     ]

# @router.get("/conversations/{conversation_id}/messages")
# def get_messages(conversation_id: int, db: Session = Depends(get_db)):
#     conv = db.get(Conversation, conversation_id)
#     if not conv:
#         raise HTTPException(status_code=404, detail="Conversation not found")

#     rows = db.execute(
#         select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
#     ).scalars().all()

#     return [
#         {
#             "id": m.id,
#             "direction": m.direction,
#             "sender_type": m.sender_type,
#             "content": m.content,
#             "created_at": m.created_at.isoformat() if m.created_at else None
#         }
#         for m in rows
#     ]

# @router.get("/events/conversations/{conversation_id}")
# async def stream_conversation_events(conversation_id: int):
#     """
#     SSE stream: frontend will connect and receive new messages live.
#     """
#     q = await broker.subscribe(conversation_id)

#     async def gen():
#         try:
#             # initial ping so browser connects immediately
#             yield "event: ping\ndata: {}\n\n"
#             while True:
#                 payload = await q.get()
#                 yield f"event: message\ndata: {json.dumps(payload)}\n\n"
#         finally:
#             await broker.unsubscribe(conversation_id, q)

#     return StreamingResponse(gen(), media_type="text/event-stream")

# @router.post("/debug/inbound")
# async def debug_inbound(psid: str, content: str, db: Session = Depends(get_db)):
#     """
#     Temporary: FB integration se pehle test ke liye.
#     Simulates customer inbound message.
#     """
#     # find/create customer
#     customer = db.execute(select(Customer).where(Customer.psid == psid)).scalar_one_or_none()
#     if not customer:
#         customer = Customer(psid=psid)
#         db.add(customer)
#         db.commit()
#         db.refresh(customer)

#     # find/create conversation
#     conv = db.execute(select(Conversation).where(Conversation.customer_id == customer.id)).scalar_one_or_none()
#     if not conv:
#         conv = Conversation(customer_id=customer.id, status="BOT_ACTIVE")
#         db.add(conv)
#         db.commit()
#         db.refresh(conv)

#     # save inbound message
#     msg = Message(conversation_id=conv.id, direction="inbound", sender_type="customer", content=content)
#     db.add(msg)
#     # conv.updated_at = msg.created_at  # ok for MVP
#     db.commit()
#     db.refresh(msg)

#     # publish realtime event
#     await broker.publish(conv.id, {
#         "id": msg.id,
#         "direction": msg.direction,
#         "sender_type": msg.sender_type,
#         "content": msg.content,
#         "created_at": msg.created_at.isoformat() if msg.created_at else None
#     })

#     return {"ok": True, "conversation_id": conv.id, "message_id": msg.id}

# @router.post("/debug/outbound")
# async def debug_outbound(conversation_id: int, content: str, sender_type: str = "bot", db: Session = Depends(get_db)):
#     """
#     Temporary: simulate bot/admin outbound message.
#     """
#     conv = db.get(Conversation, conversation_id)
#     if not conv:
#         raise HTTPException(status_code=404, detail="Conversation not found")

#     msg = Message(conversation_id=conversation_id, direction="outbound", sender_type=sender_type, content=content)
#     db.add(msg)
#     db.commit()
#     db.refresh(msg)

#     await broker.publish(conversation_id, {
#         "id": msg.id,
#         "direction": msg.direction,
#         "sender_type": msg.sender_type,
#         "content": msg.content,
#         "created_at": msg.created_at.isoformat() if msg.created_at else None
#     })

#     return {"ok": True, "message_id": msg.id}

# # @router.get("/orders/{order_id}")
# # def get_order(order_id: str, db: Session = Depends(get_db)):
# #     order = db.execute(select(Order).where(Order.order_id == order_id)).scalar_one_or_none()
# #     if not order:
# #         return {"found": False}
# #     return {"found": True, "order_id": order.order_id, "status": order.status, "eta": order.eta}


# edit 2

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Conversation, Message, Customer
from app.realtime.broker import broker


router = APIRouter(prefix="/api", tags=["chat"])

@router.get("/conversations")
def list_conversations(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Conversation, Customer)
        .join(Customer, Customer.id == Conversation.customer_id)
        .order_by(Conversation.updated_at.desc())
    ).all()

    out = []
    for conv, cust in rows:
        out.append({
            "id": conv.id,
            "customer_id": conv.customer_id,
            "customer_name": cust.fb_name or f"Customer {conv.customer_id}",
            "status": conv.status,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None
        })
    return out

@router.get("/conversations/{conversation_id}/messages")
def get_messages(conversation_id: int, db: Session = Depends(get_db)):
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    rows = db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
    ).scalars().all()

    return [
        {
            "id": m.id,
            "direction": m.direction,
            "sender_type": m.sender_type,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in rows
    ]

@router.get("/events/conversations/{conversation_id}")
async def stream_conversation_events(conversation_id: int):
    """
    SSE stream: frontend will connect and receive new messages live.
    """
    q = await broker.subscribe(conversation_id)

    async def gen():
        try:
            # initial ping so browser connects immediately
            yield "event: ping\ndata: {}\n\n"
            while True:
                payload = await q.get()
                yield f"event: message\ndata: {json.dumps(payload)}\n\n"
        finally:
            await broker.unsubscribe(conversation_id, q)

    return StreamingResponse(gen(), media_type="text/event-stream")

@router.post("/debug/inbound")
async def debug_inbound(psid: str, content: str, db: Session = Depends(get_db)):
    """
    Temporary: FB integration se pehle test ke liye.
    Simulates customer inbound message.
    """
    # find/create customer
    customer = db.execute(select(Customer).where(Customer.psid == psid)).scalar_one_or_none()
    if not customer:
        customer = Customer(psid=psid)
        db.add(customer)
        db.commit()
        db.refresh(customer)

    # find/create conversation
    conv = db.execute(select(Conversation).where(Conversation.customer_id == customer.id)).scalar_one_or_none()
    if not conv:
        conv = Conversation(customer_id=customer.id, status="BOT_ACTIVE")
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # save inbound message
    msg = Message(conversation_id=conv.id, direction="inbound", sender_type="customer", content=content)
    db.add(msg)
    # conv.updated_at = msg.created_at  # ok for MVP
    db.commit()
    db.refresh(msg)

    # publish realtime event
    await broker.publish(conv.id, {
        "id": msg.id,
        "direction": msg.direction,
        "sender_type": msg.sender_type,
        "content": msg.content,
        "created_at": msg.created_at.isoformat() if msg.created_at else None
    })

    return {"ok": True, "conversation_id": conv.id, "message_id": msg.id}

@router.post("/debug/outbound")
async def debug_outbound(conversation_id: int, content: str, sender_type: str = "bot", db: Session = Depends(get_db)):
    """
    Temporary: simulate bot/admin outbound message.
    """
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg = Message(conversation_id=conversation_id, direction="outbound", sender_type=sender_type, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)

    await broker.publish(conversation_id, {
        "id": msg.id,
        "direction": msg.direction,
        "sender_type": msg.sender_type,
        "content": msg.content,
        "created_at": msg.created_at.isoformat() if msg.created_at else None
    })

    return {"ok": True, "message_id": msg.id}

# @router.get("/orders/{order_id}")
# def get_order(order_id: str, db: Session = Depends(get_db)):
#     order = db.execute(select(Order).where(Order.order_id == order_id)).scalar_one_or_none()
#     if not order:
#         return {"found": False}
#     return {"found": True, "order_id": order.order_id, "status": order.status, "eta": order.eta}
