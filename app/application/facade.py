from decimal import Decimal
from typing import List, Optional

from app.domain.entities import Customer, Account, Transaction
from app.domain.exceptions import ValidationError, NotFoundError
from app.repositories.base import CustomerRepository, AccountRepository, TransactionRepository

from app.services.transfer_service import TransferService
from app.services.deposit_service import DepositService
from app.services.withdraw_service import WithdrawService

class BankingFacade:
    def __init__(
        self,
        customer_repo: CustomerRepository,
        account_repo: AccountRepository,
        transaction_repo: TransactionRepository,
        transfer_service: TransferService,
        deposit_service: DepositService, 
        withdraw_service: WithdrawService 
    ):
        self.customer_repo = customer_repo
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo
        self.transfer_service = transfer_service
        self.deposit_service = deposit_service
        self.withdraw_service = withdraw_service

    def create_customer(self, name: str, email: str) -> Customer:
        customer = Customer(name=name, email=email)
        self.customer_repo.add(customer)
        return customer

    def create_account(self, customer_id: str, currency: str = "USD") -> Account:
        customer = self.customer_repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Cliente {customer_id} no encontrado")
        
        account = Account(customer_id=customer_id, currency=currency)
        self.account_repo.add(account)
        return account

    def deposit(self, account_id: str, amount: Decimal) -> Transaction:
        try:
            return self.deposit_service.execute(account_id, amount)
        except Exception as e:
            raise ValidationError(f"Error en depósito: {str(e)}")

    def withdraw(self, account_id: str, amount: Decimal) -> Transaction:
        try:
            return self.withdraw_service.execute(account_id, amount)
        except Exception as e:
            raise ValidationError(f"Error en retiro: {str(e)}")

    def transfer(self, from_account: str, to_account: str, amount: Decimal) -> Transaction:
        try:
            return self.transfer_service.execute(from_account, to_account, amount)
        except Exception as e:
            raise ValidationError(f"Error en transferencia: {str(e)}")

    def get_account(self, account_id: str) -> Optional[Account]:
        return self.account_repo.get_by_id(account_id)

    def list_transactions(self, account_id: str, limit: int = 10, offset: int = 0) -> List[Transaction]:
        transactions = self.transaction_repo.list_by_account(account_id)

        return transactions[offset : offset + limit]