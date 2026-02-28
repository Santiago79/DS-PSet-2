from app.domain.entities import Customer
from app.domain.exceptions import DuplicateEmailError

from app.repositories.base import CustomerRepository

class CustomerService:
    def __init__(self, repo: CustomerRepository) -> None:
        self.repo = repo

    def create_customer(self, name: str, email: str) -> Customer:
        email_norm = email.strip().lower()
        if self.repo.get_by_email(email_norm) is not None:
            raise DuplicateEmailError(f"Ya existe un cliente con el email '{email}'")
        customer = Customer(name=name.strip(), email=email_norm, active=True)
        self.repo.add(customer)
        return customer
