"""Dependencias de FastAPI: sesión de BD, BankingFacade y mapeo de excepciones a HTTP."""
from decimal import Decimal

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from app.infra.database import get_db
from app.application.facade import BankingFacade
from app.repositories.sqlalchemy_repo import (
    SQLCustomerRepository,
    SQLAccountRepository,
    SQLTransactionRepository,
)
from app.services.deposit_service import DepositService
from app.services.withdraw_service import WithdrawService
from app.services.transfer_service import TransferService
from app.services.fee_strategies import NoFeeStrategy
from app.services.risk_strategies import MaxAmountRule, VelocityRule, DailyLimitRule
from app.domain.exceptions import (
    BankingError,
    ValidationError,
    NotFoundError,
    InsufficientFundsError,
    AccountNotOperableError,
    TransactionRejectedError,
    InvalidStatusTransition,
    DuplicateEmailError,
)
from app.services.configuration_service import ConfigurationService 

_config_service = ConfigurationService()


def get_config_service() -> ConfigurationService:
    """Dependency para obtener el servicio de configuración (siempre la misma instancia)"""
    return _config_service

def get_facade(session: Session = Depends(get_db),
               config_service: ConfigurationService = Depends(get_config_service)) -> BankingFacade:
    """Construye BankingFacade con repos SQL y servicios (fee/risk por defecto)."""
    customer_repo = SQLCustomerRepository(session)
    account_repo = SQLAccountRepository(session)
    transaction_repo = SQLTransactionRepository(session)

    fee_strategy = NoFeeStrategy()
    risk_strategies = [
        MaxAmountRule(),
        VelocityRule(max_transactions=5, time_window_minutes=10),
        DailyLimitRule(daily_limit=Decimal("2000")),
    ]

    deposit_service = DepositService(
        account_repo=account_repo,
        transaction_repo=transaction_repo,
        fee_strategy=fee_strategy,
        risk_strategies=risk_strategies,
    )
    withdraw_service = WithdrawService(
        account_repo=account_repo,
        transaction_repo=transaction_repo,
        fee_strategy=fee_strategy,
        risk_strategies=risk_strategies,
    )
    transfer_service = TransferService(
        account_repo=account_repo,
        transaction_repo=transaction_repo,
        fee_strategy=fee_strategy,
        risk_strategies=risk_strategies,
    )

    return BankingFacade(
        customer_repo=customer_repo,
        account_repo=account_repo,
        transaction_repo=transaction_repo,
        transfer_service=transfer_service,
        deposit_service=deposit_service,
        withdraw_service=withdraw_service,
        config_service=config_service,  
    )


def to_http(e: Exception) -> HTTPException:
    """Mapea excepciones de dominio a HTTP (400, 403, 404, 500)."""
    if isinstance(e, NotFoundError):
        return HTTPException(status_code=404, detail=e.message)
    if isinstance(e, InsufficientFundsError):
        return HTTPException(status_code=400, detail=e.message)
    if isinstance(e, AccountNotOperableError):
        return HTTPException(status_code=403, detail=e.message)
    if isinstance(e, (TransactionRejectedError, ValidationError, InvalidStatusTransition, DuplicateEmailError)):
        return HTTPException(status_code=400, detail=e.message)
    if isinstance(e, BankingError):
        return HTTPException(status_code=500, detail=e.message)
    return HTTPException(status_code=500, detail="Internal Server Error")
