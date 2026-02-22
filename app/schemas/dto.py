from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ValidationInfo

from app.domain.enums import AccountStatus, TransactionStatus, TransactionType

# Customer

class CustomerCreateRequest(BaseModel):
    name: str = Field(min_length=2, description="Nombre completo del cliente")
    email: str = Field(description="Correo electrónico del cliente")

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El nombre no puede estar vacío o contener solo espacios en blanco")
        return v.strip()

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str) -> str:
        if not v or "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Formato de correo electrónico inválido")
        return v.strip().lower()

class CustomerResponse(BaseModel):
    id: str
    name: str
    email: str
    status: str


# Account 

class AccountCreateRequest(BaseModel):
    customer_id: str = Field(min_length=1, description="ID del cliente que posee la cuenta")

class AccountResponse(BaseModel):
    id: str
    customer_id: str
    currency: str
    balance: float
    status: AccountStatus


# Transaction (deposit / withdraw / transfer) 

class DepositRequest(BaseModel):
    account_id: str = Field(min_length=1, description="ID de la cuenta destino")
    amount: float = Field(gt=0, description="Monto a depositar")

class WithdrawRequest(BaseModel):
    account_id: str = Field(min_length=1, description="ID de la cuenta de la cual retirar")
    amount: float = Field(gt=0, description="Monto a retirar")

class TransferRequest(BaseModel):
    from_account_id: str = Field(min_length=1, description="ID de la cuenta origen")
    to_account_id: str = Field(min_length=1, description="ID de la cuenta destino")
    amount: float = Field(gt=0, description="Monto a transferir")

    @field_validator("to_account_id")
    @classmethod
    def from_and_to_different(cls, v: str, info: ValidationInfo) -> str:
        if info.data and info.data.get("from_account_id") == v:
            raise ValueError("from_account_id y to_account_id deben ser diferentes")
        return v

class TransactionResponse(BaseModel):
    id: str
    type: TransactionType
    amount: float
    currency: str
    status: TransactionStatus
    created_at: datetime