from operator import attrgetter

import attr

from .exceptions import LackOfMoney
from .models import Customer, Account, Transaction, Operation, AccountOperations
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
            if credit_account.balance < txn.amount:
                raise LackOfMoney(f'Lack of money on account {txn.credit_account_id}.')

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
        # Check that customer exists
        self._repository.get_customer(customer_id)
        return self._repository.get_customer_accounts(customer_id)

    def get_account_operations(self, account_id):
        # Check that account exists
        account = self._repository.get_account(account_id)
        txns = self._repository.get_transactions(account_id)
        txns = sorted(
            txns,
            key=attrgetter('create_date')
        )
        operations = [
            Operation.from_txn(txn, account)
            for txn in txns
        ]
        balance = 0
        for operation in operations:
            balance += operation.amount
            operation.balance = balance

        operations.reverse()

        return AccountOperations(
            account.id,
            account.balance,
            account.create_date,
            account.customer_id,
            operations)
