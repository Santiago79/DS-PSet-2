from __future__ import annotations
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from app.domain.enums import AccountStatus, TransactionStatus, TransactionType

Base = declarative_base()

class CustomerModel(Base):
    __tablename__ = "customers"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    status = Column(String, default="ACTIVE")
    accounts = relationship("AccountModel", back_populates="customer")

class AccountModel(Base):
    __tablename__ = "accounts"
    id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    currency = Column(String, default="USD")
    balance = Column(Float, default=0.0)
    status = Column(SQLEnum(AccountStatus), default=AccountStatus.ACTIVE) 
    
    customer = relationship("CustomerModel", back_populates="accounts")
    transactions = relationship("TransactionModel", back_populates="account")

class TransactionModel(Base):
    __tablename__ = "transactions"
    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    target_account_id = Column(String, nullable=True) 
    type = Column(SQLEnum(TransactionType), nullable=False) 
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("AccountModel", back_populates="transactions")