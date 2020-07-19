import attr

from .exceptions import NotFound
from .models import Customer, Account, Transaction
from .repository import BillingRepository

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

    def apply_txn(self, txn: Transaction):
        session = self._repository.begin()

        if txn.credit_account_id:
            credit_account = session.get_account(txn.credit_account_id)
            credit_account.balance = credit_account.balance - txn.amount
            session.update_account(credit_account)

        debit_account = session.get_account(txn.debit_account_id)
        debit_account.balance = debit_account.balance + txn.amount
        session.update_account(debit_account)

        session.save_txn(txn)
        session.commit()

    def get_customers(self):
        return self._repository.get_customers()

    def get_customer_accounts(self, customer_id):
        customer = self._repository.get_customer(customer_id)
        if not customer:
            raise NotFound('Customer not found.')
        return self._repository.get_customer_accounts(customer_id)
