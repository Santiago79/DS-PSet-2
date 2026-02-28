from __future__ import annotations
from typing import Optional
from sqlalchemy import String, ForeignKey, Float, Enum as SQLEnum, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from app.domain.enums import AccountStatus, TransactionStatus, LedgerDirection, TransactionType
from datetime import datetime

class Base(DeclarativeBase):
    pass

class CustomerModel(Base):
    __tablename__ = "customers"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    
    accounts: Mapped[list[AccountModel]] = relationship(back_populates="customer")

class AccountModel(Base):
    __tablename__ = "accounts"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[AccountStatus] = mapped_column(SQLEnum(AccountStatus), default=AccountStatus.ACTIVE)
    
    customer: Mapped[CustomerModel] = relationship(back_populates="accounts")
    transactions: Mapped[list[TransactionModel]] = relationship(back_populates="account")

class TransactionModel(Base):
    __tablename__ = "transactions"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    target_account_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType))
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    account: Mapped[AccountModel] = relationship(back_populates="transactions")