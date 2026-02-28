from decimal import Decimal
from uuid import UUID

from app.domain.entities import Account, Transaction
from app.domain.enums import TransactionStatus, TransactionType
from app.domain.exceptions import (
    InsufficientFundsError,
    TransactionRejectedError,
    ValidationError,
)
from app.domain.factories import TransactionFactory
from app.repositories.base import AccountRepository, TransactionRepository
from app.services.fee_strategies import FeeStrategy
from app.services.risk_strategies import RiskStrategy


class TransferService:
    """Servicio para realizar transferencias entre cuentas.
    
    Implementa el caso de uso de transferencia requerido en el PDF (sección 3.2).
    """
    
    def __init__(
        self,
        account_repo: AccountRepository,
        transaction_repo: TransactionRepository,
        fee_strategy: FeeStrategy,
        risk_strategies: list[RiskStrategy],
    ):
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo
        self.fee_strategy = fee_strategy
        self.risk_strategies = risk_strategies
    
    def execute(
        self, 
        from_account_id: UUID, 
        to_account_id: UUID, 
        amount: Decimal
    ) -> Transaction:
     
        # Validaciones básicas
        if amount <= 0:
            raise ValidationError("El monto de la transferencia debe ser mayor a cero")
        
        if from_account_id == to_account_id:
            raise ValidationError("La cuenta origen y destino no pueden ser la misma")
        
        # 1. Obtener ambas cuentas
        from_account = self.account_repo.get_by_id(str(from_account_id))
        if not from_account:
            raise ValidationError(f"Cuenta origen {from_account_id} no encontrada")
        
        to_account = self.account_repo.get_by_id(str(to_account_id))
        if not to_account:
            raise ValidationError(f"Cuenta destino {to_account_id} no encontrada")
        
        # 2. Verificar que ambas cuentas puedan operar
        from_account.check_can_operate()
        to_account.check_can_operate()
        
        # 3. Crear transacción (PENDING)
        transaction = TransactionFactory.get_creator(TransactionType.TRANSFER).create(
            amount, from_account_id, target_account_id=to_account_id
        )
        self.transaction_repo.add(transaction)
        
        try:
            # 4. Calcular comisión (se aplica a la cuenta origen)
            fee = self.fee_strategy.calculate_fee(amount)
            total_to_debit = amount + fee
            
            # 5. Verificar fondos suficientes en origen (incluyendo comisión)
            if from_account.balance < total_to_debit:
                raise InsufficientFundsError(
                    f"Fondos insuficientes en cuenta origen. Saldo: {from_account.balance}, "
                    f"Requerido: {total_to_debit} (monto: {amount} + comisión: {fee})"
                )
            
            # 6. Obtener transacciones recientes para reglas de riesgo (de la cuenta origen)
            recent = self.transaction_repo.list_recent(str(from_account_id), minutes=60)
            
            # 7. Aplicar TODAS las reglas de riesgo
            for rule in self.risk_strategies:
                is_valid, message = rule.validate(transaction, from_account, recent)
                if not is_valid:
                    # Rechazar transacción
                    transaction.transition_to(TransactionStatus.REJECTED)
                    self.transaction_repo.update_status(transaction.id, transaction.status)
                    raise TransactionRejectedError(message)
            
            # 8. Aplicar la transferencia (atómica)
            # 8a. Debitar de origen (monto + comisión)
            from_account.apply_debit(total_to_debit)
            self.account_repo.update(from_account)
            
            # 8b. Acreditar a destino (solo el monto, la comisión no va a destino)
            to_account.apply_credit(amount)
            self.account_repo.update(to_account)
            
            # 9. Aprobar transacción
            transaction.transition_to(TransactionStatus.APPROVED)
            self.transaction_repo.update_status(transaction.id, transaction.status)
            
            return transaction
            
        except Exception as e:
            # Si algo falla, aseguramos que la transacción quede REJECTED
            if transaction.status != TransactionStatus.REJECTED:
                transaction.transition_to(TransactionStatus.REJECTED)
                self.transaction_repo.update_status(transaction.id, transaction.status)
            raise e