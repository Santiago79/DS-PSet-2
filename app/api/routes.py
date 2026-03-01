"""Endpoints FastAPI para Customer, Account y Transacciones. Toda la lógica pasa por BankingFacade."""
from fastapi import APIRouter, Depends, Query

from app.application.facade import BankingFacade
from app.api.deps import get_facade, to_http
from app.domain.exceptions import NotFoundError
from app.schemas.dto import (
    CustomerCreateRequest,
    CustomerResponse,
    AccountCreateRequest,
    AccountResponse,
    DepositRequest,
    WithdrawRequest,
    TransferRequest,
    TransactionResponse,
)

router = APIRouter()


# ---------- Customers ----------

@router.post(
    "/customers",
    response_model=CustomerResponse,
    status_code=201,
    summary="Crear cliente",
    description="Crea un nuevo cliente (customer). Retorna el cliente con id asignado.",
)
def create_customer(
    body: CustomerCreateRequest,
    facade: BankingFacade = Depends(get_facade),
):
    try:
        customer = facade.create_customer(name=body.name, email=body.email)
        return CustomerResponse(
            id=customer.id,
            name=customer.name,
            email=customer.email,
            status=customer.status,
        )
    except Exception as e:
        raise to_http(e)


# ---------- Accounts ----------

@router.post(
    "/accounts",
    response_model=AccountResponse,
    status_code=201,
    summary="Crear cuenta",
    description="Crea una nueva cuenta para un cliente existente. Moneda por defecto USD.",
)
def create_account(
    body: AccountCreateRequest,
    facade: BankingFacade = Depends(get_facade),
):
    try:
        account = facade.create_account(customer_id=body.customer_id, currency="USD")
        return AccountResponse(
            id=account.id,
            customer_id=account.customer_id,
            currency=account.currency,
            balance=account.balance,
            status=account.status,
        )
    except Exception as e:
        raise to_http(e)


@router.get(
    "/accounts/{account_id}",
    response_model=AccountResponse,
    summary="Obtener cuenta",
    description="Retorna el detalle de una cuenta por su ID. 404 si no existe.",
)
def get_account(
    account_id: str,
    facade: BankingFacade = Depends(get_facade),
):
    try:
        account = facade.get_account(account_id)
        if not account:
            raise NotFoundError(f"Cuenta {account_id} no encontrada")
        return AccountResponse(
            id=account.id,
            customer_id=account.customer_id,
            currency=account.currency,
            balance=account.balance,
            status=account.status,
        )
    except Exception as e:
        raise to_http(e)


# ---------- Transactions ----------

@router.post(
    "/transactions/deposit",
    response_model=TransactionResponse,
    status_code=201,
    summary="Depositar",
    description="Deposita un monto en una cuenta. Errores: 400 (validación/risk), 403 (cuenta congelada), 404 (cuenta no encontrada).",
)
def deposit(
    body: DepositRequest,
    facade: BankingFacade = Depends(get_facade),
):
    try:
        transaction = facade.deposit(account_id=body.account_id, amount=body.amount)
        return TransactionResponse(
            id=transaction.id,
            type=transaction.type,
            amount=transaction.amount,
            currency=getattr(transaction, "currency", "USD"),
            status=transaction.status,
            created_at=transaction.created_at,
        )
    except Exception as e:
        raise to_http(e)


@router.post(
    "/transactions/withdraw",
    response_model=TransactionResponse,
    status_code=201,
    summary="Retirar",
    description="Retira un monto de una cuenta. 400 si fondos insuficientes; 403 si cuenta congelada/cerrada.",
)
def withdraw(
    body: WithdrawRequest,
    facade: BankingFacade = Depends(get_facade),
):
    try:
        transaction = facade.withdraw(account_id=body.account_id, amount=body.amount)
        return TransactionResponse(
            id=transaction.id,
            type=transaction.type,
            amount=transaction.amount,
            currency=getattr(transaction, "currency", "USD"),
            status=transaction.status,
            created_at=transaction.created_at,
        )
    except Exception as e:
        raise to_http(e)


@router.post(
    "/transactions/transfer",
    response_model=TransactionResponse,
    status_code=201,
    summary="Transferir",
    description="Transfiere un monto entre dos cuentas. 400 si fondos insuficientes o reglas de riesgo; 403 si alguna cuenta no operable.",
)
def transfer(
    body: TransferRequest,
    facade: BankingFacade = Depends(get_facade),
):
    try:
        transaction = facade.transfer(
            from_account=body.from_account_id,
            to_account=body.to_account_id,
            amount=body.amount,
        )
        return TransactionResponse(
            id=transaction.id,
            type=transaction.type,
            amount=transaction.amount,
            currency=getattr(transaction, "currency", "USD"),
            status=transaction.status,
            created_at=transaction.created_at,
        )
    except Exception as e:
        raise to_http(e)


@router.get(
    "/accounts/{account_id}/transactions",
    response_model=list[TransactionResponse],
    summary="Listar transacciones de una cuenta",
    description="Lista las transacciones de la cuenta con paginación (limit y offset).",
)
def list_account_transactions(
    account_id: str,
    facade: BankingFacade = Depends(get_facade),
    limit: int = Query(10, ge=1, le=100, description="Cantidad máxima de registros"),
    offset: int = Query(0, ge=0, description="Registros a saltar"),
):
    try:
        account = facade.get_account(account_id)
        if not account:
            raise NotFoundError(f"Cuenta {account_id} no encontrada")
        transactions = facade.list_transactions(account_id=account_id, limit=limit, offset=offset)
        return [
            TransactionResponse(
                id=t.id,
                type=t.type,
                amount=t.amount,
                currency=getattr(t, "currency", "USD"),
                status=t.status,
                created_at=t.created_at,
            )
            for t in transactions
        ]
    except Exception as e:
        raise to_http(e)
