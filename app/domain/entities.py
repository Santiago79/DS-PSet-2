from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from app.domain.enums import AccountStatus, TransactionStatus, TransactionType

@dataclass
class Customer:
    id: str
    name: str
    email: str
    status: str = "ACTIVE"

@dataclass
class Account:
    id: str
    customer_id: str
    currency: str = "USD"
    _balance: Decimal = Decimal("0.0")
    status: AccountStatus = AccountStatus.ACTIVE

    @property
    def balance(self) -> Decimal:
        return self._balance

@dataclass
class Transaction:
    id: str
    account_id: str
    amount: Decimal
    type: TransactionType
    status: TransactionStatus = TransactionStatus.PENDING
    target_account_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    # NUEVO: Campo para el Builder y persistencia JSON
    metadata: Optional[Dict[str, Any]] = None