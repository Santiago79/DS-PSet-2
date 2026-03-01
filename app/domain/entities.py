from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from decimal import Decimal
from typing import Optional, Dict, Any

from app.domain.enums import AccountStatus, TransactionStatus, TransactionType, LedgerDirection
from app.domain.exceptions import InvalidStatusTransition, ValidationError

@dataclass
class Customer:
    name: str
    email: str
    id: str = field(default_factory=lambda: str(uuid4()))
    active: bool = True

    def __post_init__(self) -> None:
        if not self.name or len(self.name.strip()) < 2:
            raise ValidationError("El nombre del cliente debe tener al menos 2 caracteres")
        if "@" not in self.email:
            raise ValidationError("El formato del email es inválido")

@dataclass
class Account:
    customer_id: str
    currency: str
    id: str = field(default_factory=lambda: str(uuid4()))
    _balance: Decimal = field(default=Decimal("0.0"))
    _status: AccountStatus = field(default=AccountStatus.ACTIVE)

    def __post_init__(self) -> None:
        if len(self.currency) != 3:
            raise ValidationError("La moneda debe ser un código ISO de 3 caracteres (ej. USD)")

    @property
    def status(self) -> AccountStatus:
        """Propiedad para acceder al estado de forma segura"""
        return self._status

    @property
    def balance(self) -> Decimal:
        """Propiedad para acceder al balance de forma segura"""
        return self._balance

    def apply_credit(self, amount: Decimal) -> None:
        if amount <= 0:
            raise ValidationError("El monto a acreditar debe ser positivo")
        self._balance += amount

    def apply_debit(self, amount: Decimal) -> None:
        if amount <= 0:
            raise ValidationError("El monto a debitar debe ser positivo")
        if self._balance < amount:
            raise ValidationError("Fondos insuficientes para realizar el débito")
        self._balance -= amount

    def transition_to(self, new_status: AccountStatus) -> None:
        """
        Lógica de transición de estados del banco.
        Define qué cambios de estado son legales.
        """
        allowed = {
            AccountStatus.ACTIVE: {AccountStatus.FROZEN, AccountStatus.CLOSED},
            AccountStatus.FROZEN: {AccountStatus.ACTIVE, AccountStatus.CLOSED},
            AccountStatus.CLOSED: set()  # Una cuenta cerrada es un estado final
        }

        if new_status == self._status:
            return

        if new_status not in allowed[self._status]:
            raise InvalidStatusTransition(
                f"Transición de cuenta inválida: {self._status} -> {new_status}"
            )
        
        self._status = new_status

@dataclass
class Transaction:
    account_id: str
    amount: Decimal
    type: TransactionType
    currency: str
    target_account_id: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: str(uuid4()))
    _status: TransactionStatus = field(default=TransactionStatus.PENDING)
    # CAMBIO PEDIDO: Agregado campo metadata para soportar el Builder
    metadata: Optional[Dict[str, Any]] = field(default=None)

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValidationError("El monto de la transacción debe ser mayor a cero")

    @property
    def status(self) -> TransactionStatus:
        return self._status

    def transition_to(self, new_status: TransactionStatus) -> None:
        """Mapa de transiciones para el ciclo de vida de una transacción"""
        allowed = {
            TransactionStatus.PENDING: {TransactionStatus.APPROVED, TransactionStatus.REJECTED},
            TransactionStatus.APPROVED: set(),
            TransactionStatus.REJECTED: set()
        }

        if new_status == self._status:
            return

        if new_status not in allowed[self._status]:
            raise InvalidStatusTransition(
                f"Transición de transacción inválida: {self._status} -> {new_status}"
            )
        
        self._status = new_status

@dataclass
class LedgerEntry:
    account_id: str
    transaction_id: str
    direction: LedgerDirection
    amount: Decimal
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)