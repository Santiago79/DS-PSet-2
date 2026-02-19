from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from app.domain.entities import Customer, Account, Transaction
from app.domain.enums import TransactionStatus
from app.repositories.models import CustomerModel, AccountModel, TransactionModel
from app.repositories.base import CustomerRepository, AccountRepository, TransactionRepository

class SQLCustomerRepository(CustomerRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, customer: Customer) -> None:
        model = CustomerModel(id=customer.id, name=customer.name, email=customer.email, status=customer.status)
        self.session.add(model)
        self.session.commit()

    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        model = self.session.query(CustomerModel).filter_by(id=customer_id).first()
        return Customer(id=model.id, name=model.name, email=model.email, status=model.status) if model else None

    def get_by_email(self, email: str) -> Optional[Customer]:
        """Implementación solicitada por mecueval"""
        model = self.session.query(CustomerModel).filter_by(email=email).first()
        return Customer(id=model.id, name=model.name, email=model.email, status=model.status) if model else None

    def update(self, customer: Customer) -> None:
        """Implementación solicitada por mecueval"""
        model = self.session.query(CustomerModel).filter_by(id=customer.id).first()
        if model:
            model.name = customer.name
            model.email = customer.email
            model.status = customer.status
            self.session.commit()

class SQLAccountRepository(AccountRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, account: Account) -> None:
        """Implementación solicitada por mecueval"""
        model = AccountModel(
            id=account.id, 
            customer_id=account.customer_id, 
            balance=account.balance, 
            currency=account.currency, 
            status=account.status
        )
        self.session.add(model)
        self.session.commit()

    def get_by_id(self, account_id: str) -> Optional[Account]:
        model = self.session.query(AccountModel).filter_by(id=account_id).first()
        if not model: return None
        return Account(id=model.id, customer_id=model.customer_id, _balance=model.balance, currency=model.currency, _status=model.status)

    def get_by_customer(self, customer_id: str) -> list[Account]:
        """Implementación solicitada por mecueval"""
        models = self.session.query(AccountModel).filter_by(customer_id=customer_id).all()
        return [Account(id=m.id, customer_id=m.customer_id, _balance=m.balance, currency=m.currency, _status=m.status) for m in models]

    def update(self, account: Account) -> None:
        model = self.session.query(AccountModel).filter_by(id=account.id).first()
        if model:
            model.balance = account.balance
            model.status = account.status
            self.session.commit()

    def find_by_currency(self, currency: str) -> list[Account]:
        """Implementación solicitada por mecueval"""
        models = self.session.query(AccountModel).filter_by(currency=currency).all()
        return [Account(id=m.id, customer_id=m.customer_id, _balance=m.balance, currency=m.currency, _status=m.status) for m in models]

class SQLTransactionRepository(TransactionRepository):
    """Clase completa solicitada por mecueval"""
    def __init__(self, session: Session):
        self.session = session

    def add(self, transaction: Transaction) -> None:
        model = TransactionModel(
            id=transaction.id,
            account_id=transaction.account_id,
            target_account_id=transaction.target_account_id,
            type=transaction.type,
            amount=transaction.amount,
            currency=transaction.currency,
            status=transaction.status,
            created_at=transaction.created_at
        )
        self.session.add(model)
        self.session.commit()

    def get_by_id(self, transaction_id: str) -> Optional[Transaction]:
        model = self.session.query(TransactionModel).filter_by(id=transaction_id).first()
        if not model: return None
        return Transaction(
            id=model.id, account_id=model.account_id, target_account_id=model.target_account_id,
            type=model.type, amount=model.amount, currency=model.currency, 
            status=model.status, created_at=model.created_at
        )

    def update_status(self, transaction_id: str, status: TransactionStatus) -> None:
        model = self.session.query(TransactionModel).filter_by(id=transaction_id).first()
        if model:
            model.status = status
            self.session.commit()

    def find_by_account(self, account_id: str) -> list[Transaction]:
        models = self.session.query(TransactionModel).filter_by(account_id=account_id).all()
        return [Transaction(
            id=m.id, account_id=m.account_id, target_account_id=m.target_account_id,
            type=m.type, amount=m.amount, currency=m.currency, 
            status=m.status, created_at=m.created_at
        ) for m in models]

    def find_recent(self, account_id: str, minutes: int) -> list[Transaction]:
        from datetime import datetime, timedelta
        limit = datetime.utcnow() - timedelta(minutes=minutes)
        models = self.session.query(TransactionModel).filter(
            TransactionModel.account_id == account_id,
            TransactionModel.created_at >= limit
        ).all()
        return [Transaction(
            id=m.id, account_id=m.account_id, target_account_id=m.target_account_id,
            type=m.type, amount=m.amount, currency=m.currency, 
            status=m.status, created_at=m.created_at
        ) for m in models]