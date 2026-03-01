import pytest
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.application.main import app
from app.infra.database import get_db
from app.repositories.models import Base, AccountModel
from app.domain.enums import AccountStatus


# Configuración de base de datos de prueba (SQLite in-memory)

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def reset_database():
    """
    Asegura una base de datos limpia por test
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def client():
    """
    Cliente de pruebas para la API (usa la BD en memoria)
    """
    with TestClient(app) as c:
        yield c

def _create_customer(client: TestClient, name: str = "Juan Pérez",
                     email: str = "juan@example.com") -> str:
    resp = client.post(
        "/customers",
        json={"name": name, "email": email},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"]
    return body["id"]

def _create_account(client: TestClient, customer_id: str) -> str:
    resp = client.post(
        "/accounts", 
        json={"customer_id": customer_id},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"]
    assert body["customer_id"] == customer_id
    return body["id"]

def test_create_customer_success(client: TestClient):
    resp = client.post(
        "/customers",
        json={"name": "Ana Gómez", "email": "ana@example.com"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"]
    assert data["name"] == "Ana Gómez"
    assert data["email"] == "ana@example.com"
    assert data["status"] == "active"

def test_create_account_success(client: TestClient):
    customer_id = _create_customer(client)
    resp = client.post(
        "/accounts", 
        json={"customer_id": customer_id},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"]
    assert data["customer_id"] == customer_id
    assert data["currency"] == "USD"
    assert Decimal(str(data["balance"])) == Decimal("0")


def test_deposit_happy_path(client: TestClient):
    customer_id = _create_customer(client)
    account_id = _create_account(client, customer_id)
    resp = client.post(
        "/transactions/deposit",
        json={"account_id": account_id, "amount": "100.50"},
    )
    assert resp.status_code == 201
    tx = resp.json()
    assert tx["id"]
    assert tx["type"] == "DEPOSIT"
    assert Decimal(str(tx["amount"])) == Decimal("100.50")
    assert tx["status"] == "APPROVED"

    # Verificar que el saldo de la cuenta se actualizó
    acc_resp = client.get(f"/accounts/{account_id}")
    assert acc_resp.status_code == 200
    acc = acc_resp.json()
    assert Decimal(str(acc["balance"])) == Decimal("100.50")

def test_transfer_success(client: TestClient):
    customer_id = _create_customer(client)
    from_account_id = _create_account(client, customer_id)
    to_account_id = _create_account(client, customer_id)

    # Fundear la cuenta origen
    resp_deposit = client.post(
        "/transactions/deposit",
        json={"account_id": from_account_id, "amount": "200"},
    )
    assert resp_deposit.status_code == 201

    # Ejecutar transferencia
    resp = client.post(
        "/transactions/transfer",
        json={
            "from_account_id": from_account_id,
            "to_account_id": to_account_id,
            "amount": "50",
        },
    )
    assert resp.status_code == 201
    tx = resp.json()
    assert tx["id"]
    assert tx["type"] == "TRANSFER"
    assert Decimal(str(tx["amount"])) == Decimal("50")
    assert tx["status"] == "APPROVED"

    # Verificar saldos
    acc_from = client.get(f"/accounts/{from_account_id}").json()
    acc_to = client.get(f"/accounts/{to_account_id}").json()
    
    assert Decimal(str(acc_from["balance"])) == Decimal("150")
    assert Decimal(str(acc_to["balance"])) == Decimal("50")

def test_list_transactions_paginated(client: TestClient):
    customer_id = _create_customer(client)
    account_id = _create_account(client, customer_id)

    # Crear varias transacciones
    amounts = ["10", "20", "30"]
    for amt in amounts:
        resp = client.post(
            "/transactions/deposit",
            json={"account_id": account_id, "amount": amt},
        )
        assert resp.status_code == 201

    # Pedir una página con limit y offset
    resp = client.get(f"/accounts/{account_id}/transactions", params={"limit": 2, "offset": 1})
    assert resp.status_code == 200
    txs = resp.json()

    assert len(txs) == 2
    for tx in txs:
        assert tx["id"]
        assert tx["type"] == "DEPOSIT"

def test_deposit_on_frozen_account_returns_403(client: TestClient):
    customer_id = _create_customer(client)
    account_id = _create_account(client, customer_id)

    # Congelar la cuenta directamente en la BD de pruebas
    session = TestingSessionLocal()
    try:
        account_model = session.query(AccountModel).filter_by(id=account_id).first()
        assert account_model is not None
        account_model.status = AccountStatus.FROZEN
        session.commit()
    finally:
        session.close()

    # Intentar un depósito sobre cuenta congelada
    resp = client.post(
        "/transactions/deposit",
        json={"account_id": account_id, "amount": "50"},
    )
    assert resp.status_code == 403
    body = resp.json()
    assert "No se puede operar" in body["detail"]