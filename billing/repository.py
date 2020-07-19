import logging

import attr
from sqlalchemy import (create_engine, or_)
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound

from .exceptions import BillingError, NotFound
from .models import (Customer,
                     Account,
                     Transaction,
                     Base,
                     customer_id_sequence,
                     RegisterData)


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
        customer_id_sequence.create(bind=self._engine,
                                    checkfirst=True)
        # TODO add indexes

    def release_connections(self):
        self._session_factory.remove()

    def begin(self):
        return BillingRepository(
            self._engine,
            self._session_factory,
            self._logger,
            session=self._session_factory(),
            autocommit=False
        )

    def commit(self):
        if self._session:
            try:
                self._session.commit()
            except SQLAlchemyError as err:
                self._session.rollback()
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

        account_id = f'{customer.id}:{account_name}'
        account.id = account_id
        session.add(customer)
        session.flush()
        session.add(account)

        self._commit(session)
        return RegisterData(customer_id,
                            account_id)

    def update_account(self, account):
        session = self._get_session()
        session.merge(account)
        self._commit(session)

    def save_txn(self, txn):
        session = self._get_session()
        session.add(txn)
        self._commit(session)

    def get_customer(self, customer_id):
        try:
            session = self._get_session()
            query = session.query(Customer).filter(Customer.id == customer_id)
            return query.one()
        except NoResultFound:
            raise NotFound('Customer not found')

    def get_customers(self):
        session = self._get_session()
        query = session.query(Customer)
        return query.all()

    def get_customer_accounts(self, customer_id):
        session = self._get_session()
        query = session.query(Account).filter(Account.customer_id == customer_id)
        return query.all()

    def get_account(self, account_id):
        try:
            session = self._get_session()
            query = session.query(Account).filter(Account.id == account_id)
            return query.one()
        except NoResultFound:
            raise NotFound('Account not found')

    def get_transactions(self, account_id):
        session = self._get_session()
        query = session.query(Transaction).filter(or_(
            Transaction.debit_account_id == account_id,
            Transaction.credit_account_id == account_id
        ))
        return query.all()
