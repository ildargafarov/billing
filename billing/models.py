import json
from datetime import datetime
from decimal import Decimal

import attr
from sqlalchemy import Column, BigInteger, Sequence, DateTime, ForeignKey, String, Numeric
from sqlalchemy.ext.declarative import declarative_base
from typing import List

Base = declarative_base()

_CUSTOMERS_TABLE_NAME = 'customers'
_ACCOUNTS_TABLE_NAME = 'accounts'
_TNXS_TABLE_NAME = 'transactions'

customer_id_sequence = Sequence('customer_id_seq')


class Customer(Base):
    __tablename__ = _CUSTOMERS_TABLE_NAME

    id = Column(
        BigInteger,
        primary_key=True)

    register_date = Column(
        DateTime,
        default=datetime.now)


class Account(Base):
    __tablename__ = _ACCOUNTS_TABLE_NAME

    id = Column(
        String(140),
        nullable=False,
        primary_key=True
    )

    balance = Column(
        Numeric(asdecimal=True)
    )

    create_date = Column(
        DateTime,
        default=datetime.now)

    customer_id = Column(
        BigInteger,
        ForeignKey(f'{_CUSTOMERS_TABLE_NAME}.id'))


class Transaction(Base):
    __tablename__ = _TNXS_TABLE_NAME

    id = Column(
        BigInteger,
        Sequence('transaction_id_seq'),
        primary_key=True)

    amount = Column(
        Numeric(asdecimal=True),
        nullable=False
    )

    credit_account_id = Column(
        String,
        ForeignKey(f'{_ACCOUNTS_TABLE_NAME}.id'))

    debit_account_id = Column(
        String,
        ForeignKey(f'{_ACCOUNTS_TABLE_NAME}.id'))

    create_date = Column(
        DateTime,
        default=datetime.now)

    @classmethod
    def from_dump(cls, dump: str):
        data = json.loads(dump)
        return cls(
            amount=Decimal.from_float(data["amount"]),
            credit_account_id=data["creditAccountId"],
            debit_account_id=data["debitAccountId"],
            create_date=datetime.fromtimestamp(data["createDate"])
        )

    def dump(self) -> str:
        return json.dumps({
            "amount": float(self.amount),
            "creditAccountId": self.credit_account_id,
            "debitAccountId": self.debit_account_id,
            "createDate": self.create_date.timestamp()
        })


@attr.s(slots=True, frozen=True)
class RegisterData:
    customer_id: int = attr.ib()
    current_account_id: str = attr.ib()


@attr.s
class Operation:
    amount: Decimal = attr.ib()
    balance: Decimal = attr.ib()
    date: datetime = attr.ib()

    @classmethod
    def from_txn(cls, txn, account, balance=None):
        if account.id == txn.credit_account_id:
            amount = -1 * txn.amount
        else:
            amount = txn.amount

        return cls(
            amount,
            balance,
            txn.create_date
        )


@attr.s
class AccountOperations:
    account_id: str = attr.ib()
    balance: Decimal = attr.ib()
    create_date: datetime = attr.ib()
    customer_id: int = attr.ib()
    operations: List[Operation] = attr.ib()
