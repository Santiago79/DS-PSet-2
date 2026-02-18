from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
import re

from app.domain.enums import AccountStatus, TransactionStatus, TransactionType
from app.domain.exceptions import (
    InsufficientFundsError, 
    AccountFrozenError, 
    AccountClosedError, 
    ValidationError
)

@dataclass
class Customer:
    name: str
    email: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "ACTIVE"

    def __post_init__(self) -> None:
        # Validación de nombre
        if not self.name or len(self.name.strip()) < 2:
            raise ValidationError("El nombre del cliente debe tener al menos 2 caracteres")
        
        # Validación de email simple 
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, self.email):
            raise ValidationError(f"El email '{self.email}' no es válido")

@dataclass
class Account:
    customer_id: str
    currency: str = "USD"
    id: str = field(default_factory=lambda: str(uuid4()))
    _balance: float = 0.0
    _status: AccountStatus = AccountStatus.ACTIVE

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def status(self) -> AccountStatus:
        return self._status

    def __post_init__(self) -> None:
        if self._balance < 0:
            raise ValidationError("Una cuenta no puede iniciarse con balance negativo")

    def check_can_operate(self) -> None:
        """Verifica si la cuenta está en un estado que permite transacciones """
        if self._status == AccountStatus.FROZEN:
            raise AccountFrozenError(f"La cuenta {self.id} está congelada")
        if self._status == AccountStatus.CLOSED:
            raise AccountClosedError(f"La cuenta {self.id} está cerrada")

    def apply_debit(self, amount: float) -> None:
        """Aplica un débito validando fondos suficientes [cite: 39, 67]"""
        self.check_can_operate()
        if amount <= 0:
            raise ValidationError("El monto a debitar debe ser positivo")
        if self._balance < amount:
            raise InsufficientFundsError(f"Fondos insuficientes. Saldo actual: {self._balance}")
        self._balance -= amount

    def apply_credit(self, amount: float) -> None:
        """Aplica un crédito a la cuenta [cite: 38]"""
        self.check_can_operate()
        if amount <= 0:
            raise ValidationError("El monto a acreditar debe ser positivo")
        self._balance += amount

    def change_status(self, new_status: AccountStatus) -> None:
        """Maneja las transiciones de estado de la cuenta [cite: 62, 63]"""
        #Una cuenta CLOSED no puede volver a ser ACTIVE
        if self._status == AccountStatus.CLOSED:
            raise ValidationError("No se puede reactivar una cuenta cerrada")
        self._status = new_status

@dataclass
class Transaction:
    type: TransactionType
    amount: float
    account_id: str
    target_account_id: str | None = None
    currency: str = "USD"
    id: str = field(default_factory=lambda: str(uuid4()))
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValidationError("El monto de la transacción debe ser mayor a cero")
        if self.type == TransactionType.TRANSFER and not self.target_account_id:
            raise ValidationError("Una transferencia requiere una cuenta de destino")

@dataclass
class LedgerDirection(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"
    
@dataclass
class LedgerEntry:
    account_id: str
    transaction_id: str
    direction: LedgerDirection
    amount: float
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValidationError("El monto del ledger debe ser positivo") [cite: 76]
