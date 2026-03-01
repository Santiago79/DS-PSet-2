class BankingError(Exception):
    """Excepción base para todos los errores del dominio bancario"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class ValidationError(BankingError):
    """Error cuando los datos de entrada no cumplen las reglas básicas"""
    pass

class DuplicateEmailError(BankingError):
    """Lanzada cuando ya existe un cliente con el mismo email"""
    pass

class InvalidStatusTransition(BankingError):
    """Error cuando se intenta un cambio de estado prohibido (ej. CLOSED -> ACTIVE)"""
    pass

class InsufficientFundsError(BankingError):
    """Error cuando la cuenta no tiene balance suficiente para un débito"""
    pass

class NotFoundError(BankingError):
    """Error cuando un recurso (cliente, cuenta, etc.) no existe en el repositorio"""
    pass


class AccountNotOperableError(BankingError):
    """Error cuando la cuenta está FROZEN o CLOSED y no se puede operar (mapeable a HTTP 403)"""
    pass

class TransactionRejectedError(BankingError):
    """Error cuando una transacción falla las reglas de riesgo o fraude"""
    pass

class InfrastructureError(BankingError):
    """Error para problemas técnicos de base de datos o conexión"""
    pass