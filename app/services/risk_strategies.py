from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Tuple

from app.domain.entities import Account, Transaction


class RiskStrategy(ABC):
    """Interfaz para estrategias de prevención de fraude.
    
    Implementa el patrón Strategy requerido en el PDF (sección 4.2 y 6.2).
    """
    
    @abstractmethod
    def validate(
        self, 
        transaction: Transaction, 
        account: Account, 
        recent_transactions: List[Transaction]
    ) -> Tuple[bool, str]:
        pass


class MaxAmountRule(RiskStrategy):
    """Regla de monto máximo.
    
    Rechaza transacciones con monto mayor a $1000.
    """
    
    def __init__(self, max_amount: Decimal = Decimal("1000")):
        self.max_amount = max_amount
    
    def validate(
        self, 
        transaction: Transaction, 
        account: Account, 
        recent_transactions: List[Transaction]
    ) -> Tuple[bool, str]:
        if transaction.amount > self.max_amount:
            return False, f"Monto excede el límite de ${self.max_amount}"
        return True, ""


class VelocityRule(RiskStrategy):
    """Regla de velocidad.
    
    Rechaza si hay más de 5 transacciones en los últimos 10 minutos.
    """
    
    def __init__(self, max_transactions: int = 5, time_window_minutes: int = 10):
        self.max_transactions = max_transactions
        self.time_window_minutes = time_window_minutes
    
    def validate(
        self, 
        transaction: Transaction, 
        account: Account, 
        recent_transactions: List[Transaction]
    ) -> Tuple[bool, str]:
        # Calcular el límite de tiempo
        now = datetime.utcnow()
        time_limit = now - timedelta(minutes=self.time_window_minutes)
        
        # Filtrar transacciones en la ventana de tiempo
        transactions_in_window = [
            t for t in recent_transactions 
            if t.created_at >= time_limit
        ]
        
        # Verificar si excede el límite
        if len(transactions_in_window) >= self.max_transactions:
            return False, f"Demasiadas transacciones ({len(transactions_in_window)}) en los últimos {self.time_window_minutes} minutos"
        
        return True, ""


class DailyLimitRule(RiskStrategy):
    """Regla de límite diario.
    
    Rechaza si la suma del día supera $2000.
    """
    
    def __init__(self, daily_limit: Decimal = Decimal("2000")):
        self.daily_limit = daily_limit
    
    def validate(
        self, 
        transaction: Transaction, 
        account: Account, 
        recent_transactions: List[Transaction]
    ) -> Tuple[bool, str]:
        # Calcular el inicio del día actual
        now = datetime.utcnow()
        start_of_day = datetime(now.year, now.month, now.day)
        
        # Filtrar transacciones de hoy
        today_transactions = [
            t for t in recent_transactions 
            if t.created_at >= start_of_day
        ]
        
        # Sumar montos de transacciones de hoy (incluyendo la actual)
        total_today = sum(t.amount for t in today_transactions) + transaction.amount
        
        # Verificar si excede el límite diario
        if total_today > self.daily_limit:
            return False, f"Límite diario de ${self.daily_limit} excedido (total: ${total_today})"
        
        return True, ""