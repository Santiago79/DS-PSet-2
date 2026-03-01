from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
import uuid

from app.domain.entities import Transaction
from app.domain.enums import TransactionType, TransactionStatus

class TransferBuilder:
    def __init__(self):
        self._reset()

    def _reset(self):
        self._amount = Decimal("0.0")
        self._from_account_id = None
        self._to_account_id = None
        self._metadata = {}
        self._timestamp = datetime.utcnow()

    def set_basic_info(self, amount: Decimal, from_account: str, to_account: str) -> TransferBuilder:
        self._amount = amount
        self._from_account_id = str(from_account)
        self._to_account_id = str(to_account)
        return self

    def apply_fee(self, fee_amount: Decimal) -> TransferBuilder:
        self._metadata["applied_fee"] = str(fee_amount)
        return self

    def add_risk_metadata(self, risk_result: str, risk_message: str) -> TransferBuilder:
        self._metadata["risk_assessment"] = {
            "result": risk_result,
            "message": risk_message
        }
        return self

    def set_timestamps(self) -> TransferBuilder:
        self._timestamp = datetime.utcnow()
        return self

    def build(self) -> Transaction:
        transaction = Transaction(
            id=str(uuid.uuid4()),
            account_id=self._from_account_id,
            target_account_id=self._to_account_id,
            amount=self._amount,
            type=TransactionType.TRANSFER,
            status=TransactionStatus.PENDING,
            metadata=self._metadata, # Sincronizado con entities.py
            created_at=self._timestamp
        )
        self._reset()
        return transaction