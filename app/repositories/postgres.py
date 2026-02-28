from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.domain.entities import Customer, Account, Transaction
from app.domain.enums import AccountStatus, TransactionStatus
from app.domain.exceptions import NotFoundError
from app.repositories.models import CustomerModel, AccountModel, TransactionModel

class PostgresCustomerRepo:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, customer: Customer) -> None:
        # Se incluye status al crear el modelo como pidió mecueval
        modelo = CustomerModel(
            id=customer.id,
            name=customer.name,
            email=customer.email,
            status=customer.active # Mapeo al campo de estatus del modelo
        )
        self.session.add(modelo)
        self.session.commit()

    def get_by_id(self, customer_id: str) -> Customer:
        modelo = self.session.get(CustomerModel, customer_id)
        if modelo is None:
            raise NotFoundError('Cliente no encontrado')
        return Customer(
            id=modelo.id, 
            name=modelo.name, 
            email=modelo.email, 
            active=modelo.status
        )

    def get_by_email(self, email: str) -> Customer:
        modelo = self.session.execute(
            select(CustomerModel).where(CustomerModel.email == email)
        ).scalar_one_or_none()
        if modelo is None:
            raise NotFoundError('Cliente con ese email no encontrado')
        return Customer(
            id=modelo.id, 
            name=modelo.name, 
            email=modelo.email, 
            active=modelo.status
        )

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

    def get_by_id(self, account_id: str) -> Account:
        modelo = self.session.get(AccountModel, account_id)
        if modelo is None:
            raise NotFoundError('Cuenta no encontrada')
        
        # Reconstrucción de estado inyectando valores a campos privados _
        return Account(
            id=modelo.id,
            customer_id=modelo.customer_id,
            currency=modelo.currency,
            _balance=modelo.balance,
            _status=modelo.status
        )

    def update(self, account: Account) -> None:
        modelo = self.session.get(AccountModel, account.id)
        if modelo is None:
            raise NotFoundError('Cuenta no encontrada para actualizar')
        
        modelo.balance = account.balance
        modelo.status = account.status
        self.session.commit()

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

    def get_by_id(self, transaction_id: str) -> Transaction:
        modelo = self.session.get(TransactionModel, transaction_id)
        if modelo is None:
            raise NotFoundError('Transacción no encontrada')
        
        return Transaction(
            id=modelo.id,
            account_id=modelo.account_id,
            target_account_id=modelo.target_account_id,
            amount=modelo.amount,
            type=modelo.type,
            currency="USD",
            created_at=modelo.created_at,
            _status=modelo.status
        )

    def update_status(self, transaction_id: str, status: TransactionStatus) -> None:
        modelo = self.session.get(TransactionModel, transaction_id)
        if modelo is None:
            raise NotFoundError('Transacción no encontrada')
        
        modelo.status = status
        self.session.commit()

    def list_recent(self, account_id: str, minutes: int) -> list[Transaction]:
        # Optimización solicitada: construcción directa en list comprehension
        limit = datetime.utcnow() - timedelta(minutes=minutes)
        modelos = self.session.execute(
            select(TransactionModel).where(
                TransactionModel.account_id == account_id,
                TransactionModel.created_at >= limit
            )
        ).scalars().all()
        
        return [
            Transaction(
                id=m.id, 
                account_id=m.account_id, 
                target_account_id=m.target_account_id,
                amount=m.amount, 
                type=m.type, 
                currency="USD", 
                created_at=m.created_at, 
                _status=m.status
            ) for m in modelos
        ]