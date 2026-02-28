from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.domain.entities import Customer, Account, Transaction
from app.domain.factories import TransferBuilder
from app.domain.exceptions import ValidationError, NotFoundError
from app.repositories.base import CustomerRepository, AccountRepository, TransactionRepository
from app.services.deposit_service import DepositService # Asumiendo que existe
from app.services.transfer_service import TransferService

class BankingFacade:
    def __init__(
        self,
        customer_repo: CustomerRepository,
        account_repo: AccountRepository,
        transaction_repo: TransactionRepository,
        transfer_service: TransferService,
        # Inyección de dependencias
    ):
        self.customer_repo = customer_repo
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo
        self.transfer_service = transfer_service
        self._transfer_builder = TransferBuilder() # Tu Issue #4

    def create_customer(self, name: str, email: str) -> Customer:
        """Orquesta la creación de un cliente con status ACTIVE"""
        customer = Customer(name=name, email=email)
        self.customer_repo.add(customer)
        return customer

    def create_account(self, customer_id: str) -> Account:
        """Crea una cuenta validando la existencia del cliente"""
        customer = self.customer_repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Cliente {customer_id} no encontrado")
        
        account = Account(customer_id=customer_id)
        self.account_repo.add(account)
        return account

    def transfer(self, from_id: str, to_id: str, amount: float) -> Transaction:
        """Delega en el TransferService usando tu Builder"""
        try:
            # Traduce tipos simples a dominio (Decimal)
            return self.transfer_service.execute(
                from_account_id=UUID(from_id),
                to_account_id=UUID(to_id),
                amount=Decimal(str(amount))
            )
        except Exception as e:
            # Traduce excepciones a mensajes amigables
            raise ValidationError(f"Error en transferencia: {str(e)}")

    def get_account(self, account_id: str) -> Optional[Account]:
        """Usa tu implementación de Optional de la Persona A"""
        return self.account_repo.get_by_id(account_id)

    def list_transactions(self, account_id: str, limit: int = 10, offset: int = 0) -> List[Transaction]:
        """Delega la consulta al repositorio de transacciones"""
        # Aquí se podría implementar lógica de paginación si el repo lo soporta
        return self.transaction_repo.list_by_account(account_id)[:limit]