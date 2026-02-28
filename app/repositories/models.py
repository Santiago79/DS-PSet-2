from __future__ import annotations
from typing import Optional, List, Any
from sqlalchemy import String, ForeignKey, Numeric, Enum as SQLEnum, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from app.domain.enums import AccountStatus, TransactionStatus, TransactionType
from datetime import datetime
from decimal import Decimal

class Base(DeclarativeBase):
    pass

class CustomerModel(Base):
    __tablename__ = "customers"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    
    accounts: Mapped[List[AccountModel]] = relationship(back_populates="customer")

class AccountModel(Base):
    __tablename__ = "accounts"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=Decimal("0.0"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[AccountStatus] = mapped_column(SQLEnum(AccountStatus), default=AccountStatus.ACTIVE)
    
    customer: Mapped[CustomerModel] = relationship(back_populates="accounts")
    transactions: Mapped[List[TransactionModel]] = relationship(back_populates="account")

class TransactionModel(Base):
    __tablename__ = "transactions"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    target_account_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    account: Mapped[AccountModel] = relationship(back_populates="transactions")