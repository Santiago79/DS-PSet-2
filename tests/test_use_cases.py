"""Tests unitarios para CustomerService y AccountService (repos mock)"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from app.domain.entities import Customer, Account, Transaction
from app.domain.enums import TransactionType
from app.domain.exceptions import NotFoundError, DuplicateEmailError

from app.services.customer_service import CustomerService
from app.services.account_service import AccountService

# CustomerService

def test_create_customer_ok_persiste_con_status_active():
    repo = MagicMock()
    repo.get_by_email.return_value = None
    svc = CustomerService(repo)
    customer = svc.create_customer("Juan Pérez", "juan@example.com")
    assert customer.name == "Juan Pérez"
    assert customer.email == "juan@example.com"
    assert customer.active is True
    assert customer.id
    repo.get_by_email.assert_called_once_with("juan@example.com")
    repo.add.assert_called_once()
    assert repo.add.call_args[0][0] is customer

def test_create_customer_email_duplicado_lanza_duplicate_email():
    repo = MagicMock()
    repo.get_by_email.return_value = Customer(name="Otro", email="juan@example.com", id="id-1", active=True)
    svc = CustomerService(repo)
    with pytest.raises(DuplicateEmailError):
        svc.create_customer("Juan", "juan@example.com")
    repo.add.assert_not_called()

def test_create_customer_normaliza_email_minusculas():
    repo = MagicMock()
    repo.get_by_email.return_value = None
    svc = CustomerService(repo)
    customer = svc.create_customer("Ana", "Ana@Example.COM")
    assert customer.email == "ana@example.com"


# AccountService

def test_create_account_ok_balance_cero_usd():
    customer = Customer(name="Juan", email="j@x.com", id="cust-1", active=True)
    customers = MagicMock()
    customers.get_by_id.return_value = customer
    accounts = MagicMock()
    svc = AccountService(customers, accounts, MagicMock())
    account = svc.create_account("cust-1")
    assert account.customer_id == "cust-1"
    assert account.currency == "USD"
    assert account.balance == 0.0
    assert account.id
    accounts.add.assert_called_once()
    assert accounts.add.call_args[0][0] is account

def test_create_account_cliente_no_existe_lanza_not_found():
    customers = MagicMock()
    customers.get_by_id.return_value = None
    accounts = MagicMock()
    svc = AccountService(customers, accounts, MagicMock())
    with pytest.raises(NotFoundError):
        svc.create_account("cust-inexistente")
    accounts.add.assert_not_called()

def test_get_account_ok_retorna_cuenta_con_saldo():
    account = Account(customer_id="c1", currency="USD", id="acc-1", _balance=100.5)
    accounts = MagicMock()
    accounts.get_by_id.return_value = account
    svc = AccountService(MagicMock(), accounts, MagicMock())
    result = svc.get_account("acc-1")
    assert result is account
    assert result.balance == 100.5
    accounts.get_by_id.assert_called_once_with("acc-1")

def test_get_account_no_existe_lanza_not_found():
    accounts = MagicMock()
    accounts.get_by_id.return_value = None
    svc = AccountService(MagicMock(), accounts, MagicMock())
    with pytest.raises(NotFoundError):
        svc.get_account("acc-inexistente")

def test_list_transactions_paginado_retorna_slice():
    t1 = Transaction(type=TransactionType.DEPOSIT, amount=10.0, account_id="acc-1", currency="USD", created_at=datetime(2025, 1, 1))
    t2 = Transaction(type=TransactionType.WITHDRAWAL, amount=5.0, account_id="acc-1", currency="USD", created_at=datetime(2025, 1, 2))
    t3 = Transaction(type=TransactionType.DEPOSIT, amount=20.0, account_id="acc-1", currency="USD", created_at=datetime(2025, 1, 3))
    transactions = MagicMock()
    transactions.list_by_account.return_value = [t1, t2, t3]
    svc = AccountService(MagicMock(), MagicMock(), transactions)
    page = svc.list_transactions("acc-1", limit=2, offset=0)
    assert len(page) == 2
    assert page[0].amount == 20.0
    assert page[1].amount == 5.0
    transactions.list_by_account.assert_called_once_with("acc-1")

def test_list_transactions_offset_limit():
    t1 = Transaction(type=TransactionType.DEPOSIT, amount=1.0, account_id="acc-1", currency="USD", created_at=datetime(2025, 1, 1))
    t2 = Transaction(type=TransactionType.DEPOSIT, amount=2.0, account_id="acc-1", currency="USD", created_at=datetime(2025, 1, 2))
    t3 = Transaction(type=TransactionType.DEPOSIT, amount=3.0, account_id="acc-1", currency="USD", created_at=datetime(2025, 1, 3))
    transactions = MagicMock()
    transactions.list_by_account.return_value = [t1, t2, t3]
    svc = AccountService(MagicMock(), MagicMock(), transactions)
    page = svc.list_transactions("acc-1", limit=1, offset=1)
    assert len(page) == 1
    assert page[0].amount == 2.0

def test_list_transactions_vacio():
    transactions = MagicMock()
    transactions.list_by_account.return_value = []
    svc = AccountService(MagicMock(), MagicMock(), transactions)
    assert svc.list_transactions("acc-1", limit=10, offset=0) == []