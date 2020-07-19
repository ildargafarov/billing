from txn_queue.models import Transaction
from abc import abstractmethod


class QueueClient:

    @abstractmethod
    def add(self, txn: Transaction):
        pass

    @abstractmethod
    def subscribe(self, callback, auto_ack=False):
        pass

    @abstractmethod
    def release_resources(self):
        pass
