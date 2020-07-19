from .client import QueueClient
from .models import Transaction
from .rabbitmq import RabbitQueueClient


def rabbitmq_client(host) -> QueueClient:
    return RabbitQueueClient.from_params(host)
