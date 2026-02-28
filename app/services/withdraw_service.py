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


class WithdrawService:
    """Servicio para realizar retiros de cuentas.
    
    Implementa el caso de uso de retiro 
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
    
    def execute(self, account_id: UUID, amount: Decimal) -> Transaction:
      
        # Validación básica
        if amount <= 0:
            raise ValidationError("El monto del retiro debe ser mayor a cero")
        
        # 1. Obtener la cuenta
        account = self.account_repo.get_by_id(str(account_id))
        if not account:
            raise ValidationError(f"Cuenta {account_id} no encontrada")
        
        # 2. Verificar que la cuenta pueda operar
        account.check_can_operate()
        
        # 3. Crear transacción (PENDING)
        transaction = TransactionFactory.get_creator(TransactionType.WITHDRAW).create(amount, account_id)
        self.transaction_repo.add(transaction)
        
        try:
            # 4. Calcular comisión PRIMERO (para saber el total a debitar)
            fee = self.fee_strategy.calculate_fee(amount)
            total_to_debit = amount + fee
            
            # 5. Verificar fondos suficientes (incluyendo comisión)
            if account.balance < total_to_debit:
                raise InsufficientFundsError(
                    f"Fondos insuficientes. Saldo: {account.balance}, "
                    f"Requerido: {total_to_debit} (monto: {amount} + comisión: {fee})"
                )
            
            # 6. Obtener transacciones recientes para reglas de riesgo
            recent = self.transaction_repo.find_recent(str(account_id), minutes=60)
            
            # 7. Aplicar TODAS las reglas de riesgo
            for rule in self.risk_strategies:
                is_valid, message = rule.validate(transaction, account, recent)
                if not is_valid:
                    # Rechazar transacción
                    transaction.status = TransactionStatus.REJECTED
                    self.transaction_repo.update_status(transaction.id, transaction.status)
                    raise TransactionRejectedError(message)
            
            # 8. Aplicar el retiro (monto + comisión)
            account.apply_debit(total_to_debit)
            self.account_repo.update(account)
            
            # 9. Aprobar transacción
            transaction.status = TransactionStatus.APPROVED
            self.transaction_repo.update_status(transaction.id, transaction.status)
            
            return transaction
            
        except Exception as e:
            # Si algo falla, aseguramos que la transacción quede REJECTED
            if transaction.status != TransactionStatus.REJECTED:
                transaction.status = TransactionStatus.REJECTED
                self.transaction_repo.update_status(transaction.id, transaction.status)
            raise e