from decimal import Decimal

from app.domain.entities import Account, Transaction
from app.domain.enums import AccountStatus
from app.domain.exceptions import NotFoundError

from app.repositories.base import CustomerRepository, AccountRepository, TransactionRepository

class AccountService:
    def __init__(self, customers: CustomerRepository, 
                 accounts: AccountRepository, transactions: TransactionRepository) -> None:
        self.customers = customers
        self.accounts = accounts
        self.transactions = transactions

    def create_account(self, customer_id: str) -> Account:
        if self.customers.get_by_id(customer_id) is None:
            raise NotFoundError("Cliente no encontrado")
        account = Account(
            customer_id=customer_id,
            currency="USD",
            _balance=Decimal("0"),
            _status=AccountStatus.ACTIVE,
        )
        self.accounts.add(account)
        return account

    def get_account(self, account_id: str) -> Account:
        account = self.accounts.get_by_id(account_id)
        if account is None:
            raise NotFoundError("Cuenta no encontrada")
        return account

    def list_transactions(self, account_id: str, limit: int = 10, offset: int = 0) -> list[Transaction]:
        if limit < 1:
            limit = 10
        if offset < 0:
            offset = 0
        all_tx = self.transactions.list_by_account(account_id)
        sorted_tx = sorted(all_tx, key=lambda t: t.created_at, reverse=True)
        return sorted_tx[offset : offset + limit]
