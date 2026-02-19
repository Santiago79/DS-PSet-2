from __future__ import annotations
from datetime import datetime, timedelta
from app.domain.entities import Customer, Account, Transaction
from app.domain.enums import TransactionStatus
from app.domain.exceptions import NotFoundError

class InMemoryCustomerRepo:
    def __init__(self) -> None:
        self._data: dict[str, Customer] = {}
    
    def add(self, customer: Customer) -> None:
        self._data[customer.id] = customer
    
    def get_by_id(self, customer_id: str) -> Customer:
        if customer_id not in self._data:
            raise NotFoundError('Cliente no encontrado!')
        return self._data[customer_id]

    def get_by_email(self, email: str) -> Customer:
        customer = next((c for c in self._data.values() if c.email == email), None)
        if not customer:
            raise NotFoundError('Cliente con ese email no encontrado!')
        return customer

    def update(self, customer: Customer) -> None:
        if customer.id not in self._data:
            raise NotFoundError('No se puede actualizar: Cliente no existe!')
        self._data[customer.id] = customer

class InMemoryAccountRepo:
    def __init__(self) -> None:
        self._data: dict[str, Account] = {}
    
    def add(self, account: Account) -> None:
        self._data[account.id] = account
    
    def get_by_id(self, account_id: str) -> Account:
        if account_id not in self._data:
            raise NotFoundError('Cuenta no encontrada!')
        return self._data[account_id]

    def get_by_customer(self, customer_id: str) -> list[Account]:
        return [acc for acc in self._data.values() if acc.customer_id == customer_id]

    def update(self, account: Account) -> None:
        if account.id not in self._data:
            raise NotFoundError('No se puede actualizar: Cuenta no existe!')
        self._data[account.id] = account

    def find_by_currency(self, currency: str) -> list[Account]:
        """Implementación solicitada para búsqueda por moneda"""
        return [acc for acc in self._data.values() if acc.currency == currency]

class InMemoryTransactionRepo:
    def __init__(self) -> None:
        self._data: dict[str, Transaction] = {}

    def add(self, transaction: Transaction) -> None:
        self._data[transaction.id] = transaction

    def get_by_id(self, transaction_id: str) -> Transaction:
        if transaction_id not in self._data:
            raise NotFoundError('Transacción no encontrada!')
        return self._data[transaction_id]

    def update_status(self, transaction_id: str, status: TransactionStatus) -> None:
        """Actualiza el estado de la transacción usando el Enum core"""
        if transaction_id not in self._data:
            raise NotFoundError('Transacción no encontrada para actualizar estado!')
        self._data[transaction_id].status = status

    def find_by_account(self, account_id: str) -> list[Transaction]:
        return [t for t in self._data.values() if t.account_id == account_id]

    def find_recent(self, account_id: str, minutes: int) -> list[Transaction]:
        now = datetime.utcnow()
        limit = now - timedelta(minutes=minutes)
        return [t for t in self._data.values() 
                if t.account_id == account_id and t.created_at >= limit]