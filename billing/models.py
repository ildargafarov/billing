from datetime import datetime

import attr
from sqlalchemy import Column, BigInteger, Sequence, DateTime, ForeignKey, String, Numeric
from sqlalchemy.ext.declarative import declarative_base

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

    sender_account_id = Column(
        String,
        ForeignKey(f'{_ACCOUNTS_TABLE_NAME}.id'))

    receiver_account_id = Column(
        String,
        ForeignKey(f'{_ACCOUNTS_TABLE_NAME}.id'))

    create_date = Column(
        DateTime,
        default=datetime.now)


@attr.s
class RegisterData:
    customer_id: int = attr.ib()
    current_account_id: str = attr.ib()
