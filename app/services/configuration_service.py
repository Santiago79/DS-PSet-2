from decimal import Decimal
from typing import Dict, Any

from app.services.fee_strategies import (
    FeeStrategy,
    NoFeeStrategy,
    FlatFeeStrategy,
    PercentFeeStrategy,
    TieredFeeStrategy
)
from app.services.risk_strategies import (
    MaxAmountRule,
    VelocityRule,
    DailyLimitRule
)


class ConfigurationService:
    """Servicio que mantiene la configuración actual de estrategias en memoria.
    
    Guarda qué estrategia de fee está activa y qué reglas de riesgo están habilitadas.
    Los valores de las estrategias son fijos (no configurables individualmente).
    """
    
    def __init__(self):
        # Configuración por defecto
        self._fee_type = "flat"  # "no", "flat", "percent", "tiered"
        
        self._risk_rules = {
            "max_amount": True,
            "velocity": True,
            "daily_limit": True
        }
    
    # ============================================
    # MÉTODOS PARA FEE STRATEGY
    # ============================================
    
    def get_current_fee_strategy(self) -> FeeStrategy:
        """Retorna la instancia de FeeStrategy según la configuración actual"""
        if self._fee_type == "flat":
            return FlatFeeStrategy()
        elif self._fee_type == "percent":
            return PercentFeeStrategy()
        elif self._fee_type == "tiered":
            return TieredFeeStrategy()
        else:  # "no" o cualquier otro
            return NoFeeStrategy()
    
    def set_fee_strategy(self, fee_type: str) -> None:
        """Cambia la estrategia de fee activa"""
        valid_types = ["no", "flat", "percent", "tiered"]
        if fee_type in valid_types:
            self._fee_type = fee_type
    
    def get_current_fee_type(self) -> str:
        """Retorna el tipo de fee actual (para el frontend)"""
        return self._fee_type
    
    # ============================================
    # MÉTODOS PARA RISK STRATEGIES
    # ============================================
    
    def get_current_risk_strategies(self) -> list:
        """Retorna la lista de reglas de riesgo activas"""
        strategies = []
        
        if self._risk_rules["max_amount"]:
            strategies.append(MaxAmountRule())
        
        if self._risk_rules["velocity"]:
            strategies.append(VelocityRule())
        
        if self._risk_rules["daily_limit"]:
            strategies.append(DailyLimitRule())
        
        return strategies
    
    def set_risk_rule(self, rule_name: str, enabled: bool) -> None:
        """Activa o desactiva una regla de riesgo específica"""
        if rule_name in self._risk_rules:
            self._risk_rules[rule_name] = enabled
    
    def get_risk_rules_status(self) -> Dict[str, bool]:
        """Retorna el estado de activación de cada regla de riesgo"""
        return self._risk_rules.copy()
    
    # ============================================
    # MÉTODOS PARA OBTENER CONFIGURACIÓN COMPLETA
    # ============================================
    
    def get_full_config(self) -> Dict[str, Any]:
        """Retorna toda la configuración actual (para el frontend)"""
        return {
            "fee": self._fee_type,
            "risk": self._risk_rules.copy()
        }