from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.domain.entities import Customer, Account, Transaction, LedgerEntry
from app.domain.enums import AccountStatus, TransactionStatus
from app.domain.exceptions import NotFoundError
from app.repositories.models import CustomerModel, AccountModel, TransactionModel, LedgerEntryModel

class PostgresCustomerRepo:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, customer: Customer) -> None:
        modelo = CustomerModel(
            id=customer.id,
            name=customer.name,
            email=customer.email
        )
        self.session.add(modelo)
        self.session.commit()

    def get(self, customer_id: str) -> Customer:
        modelo = self.session.get(CustomerModel, customer_id)
        if modelo is None:
            raise NotFoundError('Cliente no encontrado')
        return Customer(id=modelo.id, name=modelo.name, email=modelo.email)

    def get_by_email(self, email: str) -> Customer:
        modelo = self.session.execute(
            select(CustomerModel).where(CustomerModel.email == email)
        ).scalar_one_or_none()
        if modelo is None:
            raise NotFoundError('Cliente con ese email no encontrado')
        return Customer(id=modelo.id, name=modelo.name, email=modelo.email)

    def list(self) -> list[Customer]:
        modelos = self.session.execute(select(CustomerModel)).scalars().all()
        return [Customer(id=m.id, name=m.name, email=m.email) for m in modelos]

class PostgresAccountRepo:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, account: Account) -> None:
        modelo = AccountModel(
            id=account.id,
            customer_id=account.customer_id,
            balance=account.balance,
            currency=account.currency,
            status=account.status
        )
        self.session.add(modelo)
        self.session.commit()

    def get(self, account_id: str) -> Account:
        modelo = self.session.get(AccountModel, account_id)
        if modelo is None:
            raise NotFoundError('Cuenta no encontrada')
        
        dominio = Account(
            id=modelo.id,
            customer_id=modelo.customer_id,
            currency=modelo.currency,
            _balance=modelo.balance
        )
        
        if modelo.status != AccountStatus.ACTIVE:
            dominio.transition_to(modelo.status)
            
        return dominio

    def update(self, account: Account) -> None:
        modelo = self.session.get(AccountModel, account.id)
        if modelo is None:
            raise NotFoundError('Cuenta no encontrada para actualizar')
        
        modelo.balance = account.balance
        modelo.status = account.status
        self.session.commit()

    def list_by_customer(self, customer_id: str) -> list[Account]:
        modelos = self.session.execute(
            select(AccountModel).where(AccountModel.customer_id == customer_id)
        ).scalars().all()
        
        cuentas = []
        for m in modelos:
            dominio = Account(id=m.id, customer_id=m.customer_id, currency=m.currency, _balance=m.balance)
            if m.status != AccountStatus.ACTIVE:
                dominio.transition_to(m.status)
            cuentas.append(dominio)
        return cuentas

class PostgresTransactionRepo:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, transaction: Transaction) -> None:
        modelo = TransactionModel(
            id=transaction.id,
            account_id=transaction.account_id,
            target_account_id=transaction.target_account_id,
            type=transaction.type,
            amount=transaction.amount,
            status=transaction.status,
            created_at=transaction.created_at
        )
        self.session.add(modelo)
        self.session.commit()

    def get(self, transaction_id: str) -> Transaction:
        modelo = self.session.get(TransactionModel, transaction_id)
        if modelo is None:
            raise NotFoundError('Transacción no encontrada')
        
        dominio = Transaction(
            id=modelo.id,
            account_id=modelo.account_id,
            target_account_id=modelo.target_account_id,
            amount=modelo.amount,
            type=modelo.type,
            currency="USD",
            created_at=modelo.created_at
        )
        
        if modelo.status != TransactionStatus.PENDING:
            dominio.transition_to(modelo.status)
            
        return dominio

    def update_status(self, transaction_id: str, status: TransactionStatus) -> None:
        modelo = self.session.get(TransactionModel, transaction_id)
        if modelo is None:
            raise NotFoundError('Transacción no encontrada')
        
        modelo.status = status
        self.session.commit()

    def list_recent(self, account_id: str, minutes: int) -> list[Transaction]:
        limit = datetime.utcnow() - timedelta(minutes=minutes)
        modelos = self.session.execute(
            select(TransactionModel).where(
                TransactionModel.account_id == account_id,
                TransactionModel.created_at >= limit
            )
        ).scalars().all()
        
        return [self.get(m.id) for m in modelos]