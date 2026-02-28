from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from app.domain.entities import Customer, Account, Transaction, LedgerEntry
from app.domain.enums import TransactionStatus

class InMemoryCustomerRepo:
    def __init__(self) -> None:
        self._data: Dict[str, Customer] = {}
    
    def add(self, customer: Customer) -> None:
        self._data[customer.id] = customer
    
    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """Retorna None si no existe, cumpliendo con el nuevo Protocol"""
        return self._data.get(customer_id)

    def get_by_email(self, email: str) -> Optional[Customer]:
        """Busca por email y retorna None si no lo encuentra"""
        return next((c for c in self._data.values() if c.email == email), None)

    def list(self) -> List[Customer]:
        return list(self._data.values())

class InMemoryAccountRepo:
    def __init__(self) -> None:
        self._data: Dict[str, Account] = {}
    
    def add(self, account: Account) -> None:
        self._data[account.id] = account
    
    def get_by_id(self, account_id: str) -> Optional[Account]:
        """Retorna None en lugar de lanzar NotFoundError"""
        return self._data.get(account_id)

    def list_by_customer(self, customer_id: str) -> List[Account]:
        return [acc for acc in self._data.values() if acc.customer_id == customer_id]

    def update(self, account: Account) -> None:
        """Actualiza solo si existe, sin lanzar excepción si falla"""
        if account.id in self._data:
            self._data[account.id] = account

    def find_by_currency(self, currency: str) -> List[Account]:
        return [acc for acc in self._data.values() if acc.currency == currency]

class InMemoryTransactionRepo:
    def __init__(self) -> None:
        self._data: Dict[str, Transaction] = {}

    def add(self, transaction: Transaction) -> None:
        self._data[transaction.id] = transaction

    def get_by_id(self, transaction_id: str) -> Optional[Transaction]:
        return self._data.get(transaction_id)

    def update_status(self, transaction_id: str, status: TransactionStatus) -> None:
        """Actualiza el estado si la transacción existe"""
        transaction = self.get_by_id(transaction_id)
        if transaction:
            transaction.transition_to(status)
            self._data[transaction_id] = transaction

    def list_by_account(self, account_id: str) -> List[Transaction]:
        return [t for t in self._data.values() if t.account_id == account_id]

    def list_recent(self, account_id: str, minutes: int) -> List[Transaction]:
        limit = datetime.utcnow() - timedelta(minutes=minutes)
        return [t for t in self._data.values() 
                if t.account_id == account_id and t.created_at >= limit]

class InMemoryLedgerRepo:
    def __init__(self) -> None:
        self._data: Dict[str, LedgerEntry] = {}

    def add(self, entry: LedgerEntry) -> None:
        self._data[entry.id] = entry

    def list_by_transaction(self, transaction_id: str) -> List[LedgerEntry]:
        return [e for e in self._data.values() if e.transaction_id == transaction_id]