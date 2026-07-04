# app/models.py
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Enum, UniqueConstraint,Boolean,Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship,Mapped, mapped_column
from backend.client import Base


class AccountType(str, enum.Enum):
    freelancer = "freelancer"
    agency = "agency"


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(128), primary_key=True)  # Still maps to Firebase UID
    email = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)

    # Maps directly to the PostgreSQL Enum
    account_type = Column(Enum(AccountType), default=AccountType.freelancer, nullable=False)

    # Notice we added index=True here! This tells SQLAlchemy to create the performance index.
    # Inside your AccountModel class:
    api_key: Mapped["APIKeyModel"] = relationship(back_populates="account")

    ai_system_prompt = Column(Text, default="You are a professional assistant.")

    # Automatically handles creation and update timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship linking this account to its clients
    clients = relationship("Client", back_populates="account", cascade="all, delete-orphan")

class APIKeyModel(Base):
    __tablename__ = "api_keys"

    # serial primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # varchar(128) not null references accounts on delete cascade
    account_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False
    )

    # varchar(255) not null unique
    key_string: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # varchar(255) default 'Default Key'
    name: Mapped[str] = mapped_column(String(255), default="Default Key")

    account: Mapped["Account"] = relationship(back_populates="api_key")

    # boolean default true
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # timestamp with time zone (nullable)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # timestamp with time zone default CURRENT_TIMESTAMP
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Recreates: create index idx_api_keys_string on api_keys (key_string);
    __table_args__ = (
        Index("idx_api_keys_string", "key_string"),
    )

# 3. Update your Client model to point to 'Account' instead of 'Freelancer'
class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    # Changed from freelancer_id to account_id
    account_id = Column(String(128), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    platform_user_id = Column(String(255), nullable=False)

    account = relationship("Account", back_populates="clients")
    messages = relationship("Message", back_populates="client")

    # Prevent duplicate clients per account
    __table_args__ = (UniqueConstraint('account_id', 'platform_user_id', name='_account_client_uc'),)


# 4. Your Message model stays exactly the same as before!
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    sender_role = Column(String(50), nullable=False)
    message_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="messages")