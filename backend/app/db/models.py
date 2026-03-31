from sqlalchemy import Column, BigInteger, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Customer(Base):
    __tablename__ = "customers"
    id = Column(BigInteger, primary_key=True, index=True)
    platform = Column(Text, nullable=False, default="facebook")
    psid = Column(Text, nullable=False, unique=True, index=True)

    fb_name = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete")

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(BigInteger, primary_key=True, index=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Text, nullable=False, default="BOT_ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete")

class Message(Base):
    __tablename__ = "messages"
    id = Column(BigInteger, primary_key=True, index=True)
    conversation_id = Column(BigInteger, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    direction = Column(Text, nullable=False)     # inbound/outbound
    sender_type = Column(Text, nullable=False)   # customer/bot/admin
    content = Column(Text, nullable=False)
    platform_message_id = Column(Text, nullable=True, unique=False, index=True)  # Meta message.mid
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    conversation = relationship("Conversation", back_populates="messages")

# extra step
class BotJob(Base):
    __tablename__ = "bot_jobs"
    id = Column(BigInteger, primary_key=True, index=True)
    conversation_id = Column(BigInteger, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    inbound_message_id = Column(BigInteger, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    status = Column(Text, nullable=False, default="queued")  # queued/processing/done/failed
    attempts = Column(BigInteger, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

# class Order(Base):
#     __tablename__ = "orders"
#     id = Column(BigInteger, primary_key=True, index=True)
#     order_id = Column(Text, nullable=False, unique=True, index=True)
#     status = Column(Text, nullable=False)
#     eta = Column(Text, nullable=True)
#     last_update = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
