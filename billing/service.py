import attr

from .repository import BillingRepository
from .models import Customer, Account, Transaction
from .exceptions import NotFound

CURRENT_ACCOUNT_NAME = 'current'


@attr.s
class BillingService:
    _repository: BillingRepository = attr.ib()

    def register_customer(self):
        customer = Customer()
        current_account = Account(balance=0)
        return self._repository.register_customer(customer,
                                                  current_account,
                                                  CURRENT_ACCOUNT_NAME)

    def get_customers(self):
        return self._repository.get_customers()

    def get_customer_accounts(self, customer_id):
        with self._repository as session:
            customer = session.get_customer(customer_id)
            if not customer:
                raise NotFound('Customer not found.')
            return session.get_customer_accounts(customer_id)
