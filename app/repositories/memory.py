from __future__ import annotations
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from app.domain.entities import Customer, Account, Transaction, LedgerEntry
from app.domain.enums import TransactionStatus
from app.domain.exceptions import NotFoundError

class InMemoryCustomerRepo:
    def __init__(self) -> None:
        self._data: dict[str, Customer] = {}
    
    def add(self, customer: Customer) -> None:
        self._data[customer.id] = customer
    
    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """Sincronizado con el Protocol de base.py"""
        if customer_id not in self._data:
            raise NotFoundError('Cliente no encontrado!')
        return self._data[customer_id]

    def get_by_email(self, email: str) -> Optional[Customer]:
        customer = next((c for c in self._data.values() if c.email == email), None)
        if not customer:
            raise NotFoundError('Cliente con ese email no encontrado!')
        return customer

    def list(self) -> list[Customer]:
        return list(self._data.values())

class InMemoryAccountRepo:
    def __init__(self) -> None:
        self._data: dict[str, Account] = {}
    
    def add(self, account: Account) -> None:
        self._data[account.id] = account
    
    def get_by_id(self, account_id: str) -> Optional[Account]:
        """Sincronizado con el Protocol de base.py"""
        if account_id not in self._data:
            raise NotFoundError('Cuenta no encontrada!')
        return self._data[account_id]

    def list_by_customer(self, customer_id: str) -> list[Account]:
        return [acc for acc in self._data.values() if acc.customer_id == customer_id]

    def update(self, account: Account) -> None:
        if account.id not in self._data:
            raise NotFoundError('No se puede actualizar: Cuenta no existe!')
        self._data[account.id] = account

    def find_by_currency(self, currency: str) -> list[Account]:
        """Implementación solicitada por mecueval"""
        return [acc for acc in self._data.values() if acc.currency == currency]

class InMemoryTransactionRepo:
    def __init__(self) -> None:
        self._data: dict[str, Transaction] = {}

    def add(self, transaction: Transaction) -> None:
        self._data[transaction.id] = transaction

    def get_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Sincronizado con el Protocol de base.py"""
        if transaction_id not in self._data:
            raise NotFoundError('Transacción no encontrada!')
        return self._data[transaction_id]

    def update_status(self, transaction_id: str, status: TransactionStatus) -> None:
        """Valida las reglas de negocio antes de actualizar"""
        transaction = self.get_by_id(transaction_id)
        # Se utiliza el método transition_to de la entidad para validar el cambio legal
        transaction.transition_to(status)
        self._data[transaction_id] = transaction

    def list_by_account(self, account_id: str) -> list[Transaction]:
        return [t for t in self._data.values() if t.account_id == account_id]

    def list_recent(self, account_id: str, minutes: int) -> list[Transaction]:
        """Optimización de búsqueda temporal"""
        limit = datetime.utcnow() - timedelta(minutes=minutes)
        return [t for t in self._data.values() 
                if t.account_id == account_id and t.created_at >= limit]

class InMemoryLedgerRepo:
    def __init__(self) -> None:
        self._data: dict[str, LedgerEntry] = {}

    def add(self, entry: LedgerEntry) -> None:
        self._data[entry.id] = entry

    def list_by_transaction(self, transaction_id: str) -> list[LedgerEntry]:
        return [e for e in self._data.values() if e.transaction_id == transaction_id]