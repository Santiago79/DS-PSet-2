from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.domain.entities import Customer, Account, Transaction
from app.repositories.models import CustomerModel, AccountModel, TransactionModel

class PostgresCustomerRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, customer: Customer) -> None:
        model = CustomerModel(
            id=customer.id,
            name=customer.name,
            email=customer.email,
            status=customer.active,
        )
        self.session.add(model)
        self.session.commit()

    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        # Ahora retorna None si no se encuentra
        model = self.session.get(CustomerModel, customer_id)
        if not model:
            return None
        return Customer(
            id=model.id, 
            name=model.name, 
            email=model.email, 
            active=model.status
        )

    def get_by_email(self, email: str) -> Optional[Customer]:
        # Ahora retorna None si no se encuentra
        stmt = select(CustomerModel).where(CustomerModel.email == email)
        model = self.session.execute(stmt).scalars().first()
        if not model:
            return None
        return Customer(
            id=model.id, 
            name=model.name, 
            email=model.email, 
            active=model.status
        )

class PostgresAccountRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, account: Account) -> None:
        model = AccountModel(
            id=account.id,
            customer_id=account.customer_id,
            balance=account.balance, # Numeric(20,4)
            currency=account.currency,
            status=account.status
        )
        self.session.add(model)
        self.session.commit()

    def get_by_id(self, account_id: str) -> Optional[Account]:
        model = self.session.get(AccountModel, account_id)
        if not model:
            return None
        return Account(
            id=model.id,
            customer_id=model.customer_id,
            currency=model.currency,
            _balance=model.balance,
            status=model.status
        )

class PostgresTransactionRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, transaction: Transaction) -> None:
        model = TransactionModel(
            id=transaction.id,
            account_id=transaction.account_id,
            amount=transaction.amount,
            type=transaction.type,
            status=transaction.status,
            created_at=transaction.created_at
        )
        self.session.add(model)
        self.session.commit()

    def get_by_id(self, transaction_id: str) -> Optional[Transaction]:
        model = self.session.get(TransactionModel, transaction_id)
        if not model:
            return None
        return Transaction(
            id=model.id,
            account_id=model.account_id,
            amount=model.amount,
            type=model.type,
            status=model.status,
            created_at=model.created_at
        )