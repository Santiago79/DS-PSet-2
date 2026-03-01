from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.domain.entities import Account, Transaction, Customer
from app.domain.enums import AccountStatus, TransactionType
from app.domain.exceptions import (
    AccountNotOperableError,
    InsufficientFundsError,
    InvalidStatusTransition,
    ValidationError,
)
from app.services.withdraw_service import WithdrawService
from app.services.fee_strategies import (
    NoFeeStrategy,
    FlatFeeStrategy,
    PercentFeeStrategy,
)
from app.services.risk_strategies import MaxAmountRule, VelocityRule


# Dominio: Account / Customer / Transaction

def test_withdraw_insufficient_funds_raises_exception():
    """Retiro con fondos insuficientes debe lanzar InsufficientFundsError."""
    # Cuenta con saldo menor al requerido
    account = Account(
        customer_id="cust-1",
        currency="USD",
        _balance=Decimal("50"),
        _status=AccountStatus.ACTIVE,
    )

    account_repo = MagicMock()
    account_repo.get_by_id.return_value = account
    transaction_repo = MagicMock()
    service = WithdrawService(
        account_repo=account_repo,
        transaction_repo=transaction_repo,
        fee_strategy=NoFeeStrategy(),
        risk_strategies=[],
    )
    with pytest.raises(InsufficientFundsError):
        service.execute(account_id=account.id, amount=Decimal("100"))

def test_account_frozen_cannot_operate():
    """Cuenta FROZEN no debe permitir operaciones"""
    account = Account(
        customer_id="cust-1",
        currency="USD",
        _balance=Decimal("100"),
        _status=AccountStatus.FROZEN,
    )
    with pytest.raises(AccountNotOperableError):
        account.check_can_operate()

def test_account_closed_cannot_operate():
    """Cuenta CLOSED no debe permitir operaciones"""
    account = Account(
        customer_id="cust-1",
        currency="USD",
        _balance=Decimal("100"),
        _status=AccountStatus.CLOSED,
    )
    with pytest.raises(AccountNotOperableError):
        account.check_can_operate()

def test_account_invalid_status_transition_raises():
    """Transición inválida de estado de cuenta debe lanzar InvalidStatusTransition"""
    account = Account(
        customer_id="cust-1",
        currency="USD",
        _balance=Decimal("0"),
        _status=AccountStatus.CLOSED,
    )
    with pytest.raises(InvalidStatusTransition):
        account.transition_to(AccountStatus.ACTIVE)

def test_customer_validation_invalid_name_and_email():
    """Customer debe validar nombre mínimo y formato de email"""
    with pytest.raises(ValidationError):
        Customer(name="A", email="user@example.com")
    with pytest.raises(ValidationError):
        Customer(name="Nombre Válido", email="sin-arroba")


# Estrategias de fees (fee_strategies)

def test_flat_fee_strategy_returns_fixed_050():
    """FlatFeeStrategy debe calcular siempre 0.50"""
    strategy = FlatFeeStrategy()
    fee_small = strategy.calculate_fee(Decimal("10"))
    fee_large = strategy.calculate_fee(Decimal("1000"))
    assert fee_small == Decimal("0.50")
    assert fee_large == Decimal("0.50")

def test_percent_fee_strategy_calculates_1_5_percent():
    """PercentFeeStrategy debe calcular 1.5% del monto"""
    strategy = PercentFeeStrategy()
    amount = Decimal("100")
    fee = strategy.calculate_fee(amount)
    assert fee == Decimal("1.5")


# Estrategias de riesgo (risk_strategies)

def test_max_amount_rule_rejects_above_limit():
    """MaxAmountRule debe rechazar montos mayores a 1000."""
    rule = MaxAmountRule(max_amount=Decimal("1000"))

    account = Account(
        customer_id="cust-1",
        currency="USD",
        _balance=Decimal("5000"),
        _status=AccountStatus.ACTIVE,
    )

    tx_ok = Transaction(
        account_id=account.id,
        amount=Decimal("999.99"),
        type=TransactionType.DEPOSIT,
        currency="USD",
    )
    ok, msg = rule.validate(tx_ok, account, [])
    assert ok is True
    assert msg == ""

    tx_bad = Transaction(
        account_id=account.id,
        amount=Decimal("1500"),
        type=TransactionType.DEPOSIT,
        currency="USD",
    )
    ok, msg = rule.validate(tx_bad, account, [])
    assert ok is False
    assert "1000" in msg


def test_velocity_rule_rejects_too_many_transactions_in_window():
    """VelocityRule debe rechazar cuando hay demasiadas transacciones recientes."""
    # Umbral bajo para que el test sea más simple
    rule = VelocityRule(max_transactions=3, time_window_minutes=10)
    account = Account(
        customer_id="cust-1",
        currency="USD",
        _balance=Decimal("5000"),
        _status=AccountStatus.ACTIVE,
    )
    now = datetime.utcnow()

    # Tres transacciones dentro de la ventana de tiempo
    recent = [
        Transaction(
            account_id=account.id,
            amount=Decimal("10"),
            type=TransactionType.DEPOSIT,
            currency="USD",
            created_at=now - timedelta(minutes=1),
        ),
        Transaction(
            account_id=account.id,
            amount=Decimal("20"),
            type=TransactionType.DEPOSIT,
            currency="USD",
            created_at=now - timedelta(minutes=2),
        ),
        Transaction(
            account_id=account.id,
            amount=Decimal("30"),
            type=TransactionType.DEPOSIT,
            currency="USD",
            created_at=now - timedelta(minutes=3),
        ),
    ]

    # Transaccion nueva a validar
    new_tx = Transaction(
        account_id=account.id,
        amount=Decimal("5"),
        type=TransactionType.DEPOSIT,
        currency="USD",
    )
    ok, msg = rule.validate(new_tx, account, recent)
    assert ok is False
    assert "Demasiadas transacciones" in msg