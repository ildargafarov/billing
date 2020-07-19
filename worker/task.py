import logging

import attr
import celery

from billing import BillingService, Transaction


@attr.s
class ProcessTransaction(celery.Task):
    name: str = attr.ib()
    _billing_service: BillingService = attr.ib()
    _logger: logging.Logger = attr.ib()

    @_logger.default
    def _logger_default(self):
        return logging.getLogger(__name__)

    def run(self, txn_dump: str):
        try:
            txn = Transaction.from_dump(txn_dump)
            self._billing_service.apply_txn(txn)
        except:
            self._logger.exception('Unexpected error.')
