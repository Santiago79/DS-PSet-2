from sqlalchemy.orm import Session
from app.domain.entities import Customer, Account, Transaction
from app.repositories.models import CustomerModel, AccountModel, TransactionModel
from app.repositories.base import CustomerRepository, AccountRepository, TransactionRepository

class SQLCustomerRepository(CustomerRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, customer: Customer) -> None:
        model = CustomerModel(id=customer.id, name=customer.name, email=customer.email)
        self.session.add(model)
        self.session.commit()

    def get_by_id(self, customer_id: str) -> Customer | None:
        model = self.session.query(CustomerModel).filter_by(id=customer_id).first()
        return Customer(id=model.id, name=model.name, email=model.email) if model else None

class SQLAccountRepository(AccountRepository):
    def __init__(self, session: Session):
        self.session = session

    def update(self, account: Account) -> None:
        model = self.session.query(AccountModel).filter_by(id=account.id).first()
        if model:
            model.balance = account.balance
            model.status = account.status
            self.session.commit()

    def get_by_id(self, account_id: str) -> Account | None:
        model = self.session.query(AccountModel).filter_by(id=account_id).first()
        if not model: return None
        # Mapeo de vuelta a entidad de dominio
        return Account(customer_id=model.customer_id, currency=model.currency, 
                       id=model.id, _balance=model.balance, _status=model.status)