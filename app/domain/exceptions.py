class DomainError(Exception):
    """Error base de capa de dominio"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class NotFoundError(DomainError):
    """Lanzada cuando un recurso (cliente, cuenta) no existe"""
    pass

class ValidationError(DomainError):
    """Lanzada para errores de validación de datos (email, nombres cortos)"""
    pass

class InvalidStatusTransition(DomainError):
    """Lanzada cuando se intenta un cambio de estado no permitido"""
    pass

class InsufficientFundsError(DomainError):
    """Lanzada cuando el balance no alcanza para la operación"""
    pass

class AccountFrozenError(DomainError):
    """Lanzada si se intenta operar con una cuenta FROZEN"""
    pass

class AccountClosedError(DomainError):
    """Lanzada si se intenta operar con una cuenta CLOSED"""
    pass

class TransactionRejectedError(DomainError):
    """Lanzada cuando fallan las reglas de RiskStrategy """
    pass