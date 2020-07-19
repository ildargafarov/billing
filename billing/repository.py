import logging
from datetime import datetime
import attr
from sqlalchemy import (BigInteger, Column,
                        DateTime, MetaData,
                        String, Table, ARRAY,
                        create_engine)
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import (insert as pg_insert,
                                            array_agg as pg_array_agg)
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import mapper, sessionmaker, scoped_session
from sqlalchemy.sql import and_, select
from .exceptions import BillingError
from .models import Customer, Transaction, Account, Base, customer_id_sequence, RegisterData


class RepositoryError(BillingError):
    pass


def new_engine(
        host,
        port,
        database,
        username,
        password,
        echo=True,
        pool_size=10,
        pool_pre_ping=True,
        pool_recycle=600
):
    url = URL(
        'postgresql+psycopg2',
        host=host,
        port=port,
        database=database,
        username=username,
        password=password
    )
    return create_engine(url,
                         echo=echo,
                         pool_size=pool_size,
                         pool_pre_ping=pool_pre_ping,
                         pool_recycle=pool_recycle)


@attr.s
class BillingRepository:
    _engine = attr.ib()
    _session_factory = attr.ib()
    _logger: logging.Logger = attr.ib()
    _session = attr.ib(default=None)
    _autocommit: bool = attr.ib(default=True)

    @classmethod
    def from_params(
            cls,
            host,
            port,
            username,
            password,
            database):
        engine = new_engine(host, port, database, username, password)
        session_factory = scoped_session(sessionmaker(bind=engine))
        logger = logging.getLogger(__name__)
        return cls(
            engine,
            session_factory,
            logger
        )

    def init(self):
        Base.metadata.create_all(self._engine,
                                 checkfirst=True)

    def release_connections(self):
        self._session_factory.remove()

    def __enter__(self):
        return BillingRepository(
            self._engine,
            self._session_factory,
            self._logger,
            session=self._session_factory(),
            autocommit=False
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            try:
                if exc_type is None:
                    self._session.commit()
                else:
                    self._session.rollback()
            except SQLAlchemyError as err:
                self._logger.exception(
                    'Unexpected error during commit or rollback.')
                raise RepositoryError(str(err))
            finally:
                self._session.close()
                self._session = None

    def _commit(self, session):
        if not self._autocommit:
            # do not commit when we are in the session
            return

        try:
            session.commit()
        except SQLAlchemyError as err:
            session.rollback()
            self._logger.exception(
                'Unexpected error during commit')
            raise RepositoryError(str(err))
        finally:
            session.close()

    def _get_session(self):
        if self._session:
            return self._session

        return self._session_factory()

    def register_customer(self,
                          customer: Customer,
                          account: Account,
                          account_name: str):
        session = self._get_session()
        customer_id = session.execute(customer_id_sequence)
        customer.id = customer_id
        account.customer_id = customer_id

        account_id = f'{customer.id}/{account_name}'
        account.id = account_id
        session.add(customer)
        session.flush()
        session.add(account)

        self._commit(session)
        return RegisterData(customer_id,
                            account_id)

    def get_customer(self, customer_id):
        session = self._get_session()
        query = session.query(Customer).filter(Customer.id == customer_id)
        return query.one()

    def get_customers(self):
        session = self._get_session()
        query = session.query(Customer)
        return query.all()

    def get_customer_accounts(self, customer_id):
        session = self._get_session()
        query = session.query(Account).filter(Account.customer_id == customer_id)
        return query.all()
