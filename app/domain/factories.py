from decimal import Decimal
from uuid import UUID

from app.domain.entities import Transaction
from app.domain.enums import TransactionType, TransactionStatus
from app.domain.exceptions import ValidationError


class TransactionFactory:
    """Fábrica para crear transacciones según su tipo.
    
    Implementa el patrón Factory Method para centralizar la creación
    y validación de transacciones requerido por el PDF (sección 6.1).
    """
    
    @staticmethod
    def create_deposit(amount: Decimal, account_id: UUID) -> Transaction:
        """Crea una transacción de depósito.
    
        """
        # Validaciones 
        if amount <= 0:
            raise ValidationError("El monto del depósito debe ser mayor a cero")
        
        if not account_id:
            raise ValidationError("Se requiere account_id para un depósito")
        
        # Crear transacción usando la entidad existente
        return Transaction(
            type=TransactionType.DEPOSIT,
            amount=float(amount),
            account_id=str(account_id),
            target_account_id=None,
            currency="USD",
            status=TransactionStatus.PENDING
        )
    
    @staticmethod
    def create_withdraw(amount: Decimal, account_id: UUID) -> Transaction:
        """Crea una transacción de retiro.
        """
        # Validaciones
        if amount <= 0:
            raise ValidationError("El monto del retiro debe ser mayor a cero")
        
        if not account_id:
            raise ValidationError("Se requiere account_id para un retiro")
        
        # Crear transacción usando la entidad existente
        return Transaction(
            type=TransactionType.WITHDRAW,
            amount=float(amount),
            account_id=str(account_id),
            target_account_id=None,
            currency="USD",
            status=TransactionStatus.PENDING
        )
    
    @staticmethod
    def create_transfer(amount: Decimal, from_account: UUID, to_account: UUID) -> Transaction:
        """Crea una transacción de transferencia.
        """
        # Validaciones 
        if amount <= 0:
            raise ValidationError("El monto de la transferencia debe ser mayor a cero")
        
        if not from_account:
            raise ValidationError("Se requiere cuenta origen para una transferencia")
        
        if not to_account:
            raise ValidationError("Se requiere cuenta destino para una transferencia")
        
        if from_account == to_account:
            raise ValidationError("La cuenta origen y destino no pueden ser la misma")
        
        # Crear transacción usando la entidad existente
        return Transaction(
            type=TransactionType.TRANSFER,
            amount=float(amount),
            account_id=str(from_account),  # La cuenta origen va en account_id
            target_account_id=str(to_account),  # La cuenta destino en target_account_id
            currency="USD",
            status=TransactionStatus.PENDING
        )
