from decimal import Decimal
from uuid import UUID

from app.domain.entities import Account, Transaction
from app.domain.enums import TransactionStatus, TransactionType
from app.domain.exceptions import (
    InsufficientFundsError,
    TransactionRejectedError,
    ValidationError,
)
from app.domain.builders import TransferBuilder  # Reemplazamos la Factory por el Builder
from app.repositories.base import AccountRepository, TransactionRepository
from app.services.fee_strategies import FeeStrategy
from app.services.risk_strategies import RiskStrategy

class TransferService:
    """Servicio para realizar transferencias entre cuentas.
    
    Implementa el caso de uso de transferencia 
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
     
        # 1. Validaciones básicas
        if amount <= 0:
            raise ValidationError("El monto de la transferencia debe ser mayor a cero")
        
        if from_account_id == to_account_id:
            raise ValidationError("La cuenta origen y destino no pueden ser la misma")
        
        # 2. Obtener ambas cuentas y verificar operabilidad
        from_account = self.account_repo.get_by_id(str(from_account_id))
        if not from_account:
            raise ValidationError(f"Cuenta origen {from_account_id} no encontrada")
        
        to_account = self.account_repo.get_by_id(str(to_account_id))
        if not to_account:
            raise ValidationError(f"Cuenta destino {to_account_id} no encontrada")
        
        from_account.check_can_operate()
        to_account.check_can_operate()
        
        # 3. Calcular comisión y verificar fondos
        fee = self.fee_strategy.calculate_fee(amount)
        total_to_debit = amount + fee
        
        if from_account.balance < total_to_debit:
            raise InsufficientFundsError(
                f"Fondos insuficientes en cuenta origen. Saldo: {from_account.balance}, "
                f"Requerido: {total_to_debit} (monto: {amount} + comisión: {fee})"
            )
        
        # 4. Obtener transacciones recientes para riesgo
        recent = self.transaction_repo.list_recent(str(from_account_id), minutes=60)
        
        # 5. Evaluar Riesgo ANTES de construir (usamos un objeto temporal ligero)
        temp_tx = Transaction(
            account_id=str(from_account_id),
            target_account_id=str(to_account_id),
            amount=amount,
            type=TransactionType.TRANSFER,
            currency="USD"
        )
        
        all_valid = True
        rejection_message = ""
        
        for rule in self.risk_strategies:
            is_valid, message = rule.validate(temp_tx, from_account, recent)
            if not is_valid:
                all_valid = False
                rejection_message = message
                break
        
        # 6. Crear la transacción REAL usando ÚNICAMENTE el Builder
        builder = TransferBuilder() \
            .from_account(str(from_account_id)) \
            .to_account(str(to_account_id)) \
            .amount(amount) \
            .currency("USD") \
            .with_fee(fee)
        
        if all_valid:
            builder.with_risk_assessment("APPROVED", "Todas las reglas de riesgo pasaron")
        else:
            builder.with_risk_assessment("REJECTED", rejection_message)
        
        transaction = builder.build()
        self.transaction_repo.add(transaction)  # Nace como PENDING en la BD
        
        # 7. Flujo de Aprobación o Rechazo
        if not all_valid:
            transaction.transition_to(TransactionStatus.REJECTED)
            self.transaction_repo.update_status(transaction.id, transaction.status)
            raise TransactionRejectedError(rejection_message)
            
        try:
            # 8. Aplicar débitos y créditos (atómico)
            from_account.apply_debit(total_to_debit)
            self.account_repo.update(from_account)
            
            to_account.apply_credit(amount)
            self.account_repo.update(to_account)
            
            # 9. Aprobar transacción final si no hubo errores matemáticos
            transaction.transition_to(TransactionStatus.APPROVED)
            self.transaction_repo.update_status(transaction.id, transaction.status)
            
            return transaction
            
        except Exception as e:
            # Si SQLAlchemy o la lógica fallan, la transacción queda rechazada
            transaction.transition_to(TransactionStatus.REJECTED)
            self.transaction_repo.update_status(transaction.id, transaction.status)
            raise e