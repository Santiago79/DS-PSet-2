from abc import ABC, abstractmethod
from decimal import Decimal
from uuid import UUID

from app.domain.entities import Transaction
from app.domain.enums import TransactionType, TransactionStatus
from app.domain.exceptions import ValidationError


# 1. Clase abstracta (interfaz común)
class TransactionCreator(ABC):
    """Clase abstracta para creadores de transacciones.
    
    Define el contrato que todas las implementaciones deben seguir.
    """
    
    @abstractmethod
    def create(self, amount: Decimal, account_id: UUID, **kwargs) -> Transaction:
        
        raise NotImplementedError


# 2. Implementaciones concretas
class DepositCreator(TransactionCreator):
    """Creador de transacciones de depósito."""
    
    def create(self, amount: Decimal, account_id: UUID, **kwargs) -> Transaction:
        # Validaciones específicas de depósito
        if amount <= 0:
            raise ValidationError("El monto del depósito debe ser mayor a cero")
        
        if not account_id:
            raise ValidationError("Se requiere account_id para un depósito")
        
        return Transaction(
            type=TransactionType.DEPOSIT,
            amount=Decimal(str(amount)),
            account_id=str(account_id),
            target_account_id=None,
            currency="USD",
            _status=TransactionStatus.PENDING
        )


class WithdrawCreator(TransactionCreator):
    """Creador de transacciones de retiro."""
    
    def create(self, amount: Decimal, account_id: UUID, **kwargs) -> Transaction:
        # Validaciones específicas de retiro
        if amount <= 0:
            raise ValidationError("El monto del retiro debe ser mayor a cero")
        
        if not account_id:
            raise ValidationError("Se requiere account_id para un retiro")
        
        return Transaction(
            type=TransactionType.WITHDRAWAL,
            amount=Decimal(str(amount)),
            account_id=str(account_id),
            target_account_id=None,
            currency="USD",
            _status=TransactionStatus.PENDING
        )


class TransferCreator(TransactionCreator):
    """Creador de transacciones de transferencia."""
    
    def create(self, amount: Decimal, account_id: UUID, **kwargs) -> Transaction:
        # Obtener cuenta destino de kwargs
        target_account_id = kwargs.get('target_account_id')
        
        # Validaciones específicas de transferencia
        if amount <= 0:
            raise ValidationError("El monto de la transferencia debe ser mayor a cero")
        
        if not account_id:
            raise ValidationError("Se requiere cuenta origen para una transferencia")
        
        if not target_account_id:
            raise ValidationError("Se requiere cuenta destino para una transferencia")
        
        if account_id == target_account_id:
            raise ValidationError("La cuenta origen y destino no pueden ser la misma")
        
        return Transaction(
            type=TransactionType.TRANSFER,
            amount=Decimal(str(amount)),
            account_id=str(account_id),
            target_account_id=str(target_account_id),
            currency="USD",
            _status=TransactionStatus.PENDING
        )


# 3. Factory Method que retorna la implementación correcta
class TransactionFactory:
    """Factory Method que retorna el creador adecuado según el tipo.
    
    """
    
    @staticmethod
    def get_creator(transaction_type: TransactionType) -> TransactionCreator:
        """Retorna el creador apropiado para el tipo de transacción."""
        creators = {
            TransactionType.DEPOSIT: DepositCreator(),
            TransactionType.WITHDRAWAL: WithdrawCreator(),
            TransactionType.TRANSFER: TransferCreator(),
        }
        
        creator = creators.get(transaction_type)
        if not creator:
            raise ValidationError(f"Tipo de transacción no soportado: {transaction_type}")
        
        return creator