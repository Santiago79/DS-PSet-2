from abc import ABC, abstractmethod
from decimal import Decimal


class FeeStrategy(ABC):
    """Interfaz para estrategias de cálculo de comisiones."""
    
    @abstractmethod
    def calculate_fee(self, amount: Decimal) -> Decimal:
        """Calcula la comisión para un monto dado."""
        pass


class NoFeeStrategy(FeeStrategy):
    """Estrategia sin comisión."""
    
    def calculate_fee(self, amount: Decimal) -> Decimal:
        return Decimal("0")


class FlatFeeStrategy(FeeStrategy):
    """Estrategia de comisión fija de $0.50."""
    
    def calculate_fee(self, amount: Decimal) -> Decimal:
        return Decimal("0.50")


class PercentFeeStrategy(FeeStrategy):
    """Estrategia de comisión porcentual (1.5%)."""
    
    def calculate_fee(self, amount: Decimal) -> Decimal:
        return amount * Decimal("0.015")  # 1.5%


class TieredFeeStrategy(FeeStrategy):
    """Estrategia de comisión por rangos.
    
    - Montos < $100: 1%
    - Montos >= $100: 2%
    """
    
    def calculate_fee(self, amount: Decimal) -> Decimal:
        if amount < Decimal("100"):
            return amount * Decimal("0.01")  # 1%
        else:
            return amount * Decimal("0.02")  # 2%