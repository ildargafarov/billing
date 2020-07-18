from datetime import datetime

from sqlalchemy import Column, BigInteger, Sequence, DateTime, ForeignKey, String, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

CURRENT_ACCOUNT_NAME = 'Current'
_CUSTOMERS_TABLE_NAME = 'customers'
_ACCOUNTS_TABLE_NAME = 'accounts'
_TNXS_TABLE_NAME = 'transactions'


class Customer(Base):
    __tablename__ = _CUSTOMERS_TABLE_NAME

    id = Column(
        BigInteger,
        Sequence('customer_id_seq'),
        primary_key=True)

    register_date = Column(
        DateTime,
        default=datetime.now)


class Account(Base):
    __tablename__ = _ACCOUNTS_TABLE_NAME

    id = Column(
        BigInteger,
        Sequence('account_id_seq'),
        primary_key=True)

    name = Column(
        String(140),
        default=CURRENT_ACCOUNT_NAME,
        nullable=False
    )

    customer_id = Column(
        BigInteger,
        ForeignKey(f'{_CUSTOMERS_TABLE_NAME}.id'))

    customer = relationship(
        "Customer",
        back_populates="accounts")

    create_date = Column(
        DateTime,
        default=datetime.now)


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
        BigInteger,
        ForeignKey(f'{_ACCOUNTS_TABLE_NAME}.id'))

    receiver_account_id = Column(
        BigInteger,
        ForeignKey(f'{_ACCOUNTS_TABLE_NAME}.id'))

    account = relationship(
        "Account",
        back_populates="transactions")

    create_date = Column(
        DateTime,
        default=datetime.now)
