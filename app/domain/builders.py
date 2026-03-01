from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from uuid import uuid4

from app.domain.entities import Transaction
from app.domain.enums import TransactionType, TransactionStatus

class TransferBuilder:
    """
    BUILDER - Estilo Profe
    Permite construir una transferencia con metadatos de riesgo y comisiones.
    """

    def __init__(self) -> None:
        # Defaults razonables
        self._account_id: str = ""
        self._target_account_id: Optional[str] = None
        self._amount: Decimal = Decimal("0.0")
        self._currency: str = "USD"
        self._metadata: dict[str, Any] = {}
        self._created_at: datetime = datetime.utcnow()

    def from_account(self, value: str) -> "TransferBuilder":
        self._account_id = value
        return self

    def to_account(self, value: str) -> "TransferBuilder":
        self._target_account_id = value
        return self

    def amount(self, value: Decimal) -> "TransferBuilder":
        self._amount = value
        return self

    def currency(self, value: str) -> "TransferBuilder":
        self._currency = value
        return self

    def with_fee(self, fee_amount: Decimal) -> "TransferBuilder":
        self._metadata["applied_fee"] = str(fee_amount)
        return self

    def with_risk_assessment(self, result: str, message: str) -> "TransferBuilder":
        self._metadata["risk_assessment"] = {
            "result": result,
            "message": message,
            "validated_at": datetime.utcnow().isoformat()
        }
        return self

    def created_at(self, value: datetime) -> "TransferBuilder":
        self._created_at = value
        return self

    def build(self) -> Transaction:
        # Retorna el producto final (Transaction) inyectando la metadata
        return Transaction(
            account_id=self._account_id,
            target_account_id=self._target_account_id,
            amount=self._amount,
            type=TransactionType.TRANSFER,
            currency=self._currency,
            created_at=self._created_at,
            id=str(uuid4()),
            metadata=dict(self._metadata)
        )