from decimal import Decimal
from uuid import UUID

from app.domain.entities import Account, Transaction
from app.domain.enums import TransactionStatus, TransactionType
from app.domain.exceptions import (
    TransactionRejectedError,
    ValidationError,
)
from app.domain.factories import TransactionFactory
from app.repositories.base import AccountRepository, TransactionRepository
from app.services.strategies.fee_strategies import FeeStrategy
from app.services.strategies.risk_strategies import RiskStrategy



class DepositService:
    """Servicio para realizar depósitos en cuentas.
    
    Implementa el caso de uso de depósito 
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
        """Ejecuta un depósito en la cuenta especificada.
    
        """
        # Validación básica
        if amount <= 0:
            raise ValidationError("El monto del depósito debe ser mayor a cero")
        
        # 1. Obtener la cuenta
        account = self.account_repo.get_by_id(str(account_id))
        if not account:
            raise ValidationError(f"Cuenta {account_id} no encontrada")
        
        # 2. Verificar que la cuenta pueda operar
        account.check_can_operate()
        
        # 3. Crear transacción (PENDING)
        transaction = TransactionFactory.get_creator(TransactionType.DEPOSIT).create(amount, account_id)
        self.transaction_repo.add(transaction)
        
        try:
            # 4. Obtener transacciones recientes para reglas de riesgo
            recent = self.transaction_repo.find_recent(str(account_id), minutes=60)
            
            # 5. Aplicar TODAS las reglas de riesgo
            for rule in self.risk_strategies:
                is_valid, message = rule.validate(transaction, account, recent)
                if not is_valid:
                    # Rechazar transacción
                    transaction.status = TransactionStatus.REJECTED
                    self.transaction_repo.update_status(transaction.id, transaction.status)
                    raise TransactionRejectedError(message)
            
            # 6. Calcular comisión (si aplica)
            fee = self.fee_strategy.calculate_fee(amount)
            
            # 7. Aplicar el depósito (monto - comisión)
            account.apply_credit(amount - fee)
            self.account_repo.update(account)
            
            # 8. Aprobar transacción
            transaction.status = TransactionStatus.APPROVED
            self.transaction_repo.update_status(transaction.id, transaction.status)
            
            return transaction
            
        except Exception as e:
            # Si algo falla, aseguramos que la transacción quede REJECTED
            if transaction.status != TransactionStatus.REJECTED:
                transaction.status = TransactionStatus.REJECTED
                self.transaction_repo.update_status(transaction.id, transaction.status)
            raise e