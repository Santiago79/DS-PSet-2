from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from app.domain.entities import Transaction
from app.domain.enums import TransactionType, TransactionStatus

class TransactionFactory:
    """Fábrica para crear instancias básicas (Depósitos/Retiros)."""
    
    @staticmethod
    def create_simple_transaction(
        account_id: str,
        amount: Decimal,
        type: TransactionType
    ) -> Transaction:
        return Transaction(
            id=str(uuid.uuid4()),
            account_id=account_id,
            amount=amount,
            type=type,
            status=TransactionStatus.APPROVED if type == TransactionType.DEPOSIT else TransactionStatus.PENDING,
            created_at=datetime.utcnow(),
            metadata=None
        )