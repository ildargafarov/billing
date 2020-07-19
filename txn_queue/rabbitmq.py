from .client import QueueClient
from .models import Transaction
import attr
import pika

TXNS_QUEUE_NAME = 'transactions'


@attr.s
class RabbitQueueClient(QueueClient):
    _connection: pika.BlockingConnection = attr.ib()
    _channel = attr.ib()

    @classmethod
    def from_params(cls, host):
        params = pika.ConnectionParameters(host)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(
            queue=TXNS_QUEUE_NAME,
            durable=True)
        return cls(connection, channel)

    def add(self, txn: Transaction):
        self._channel.basic_publish(
            exchange='',
            routing_key=txn.key,
            body=txn.dump(),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )

    def subscribe(self, callback, auto_ack=False):
        self._channel.basic_consume(
            queue=TXNS_QUEUE_NAME,
            auto_ack=auto_ack,
            on_message_callback=callback)
        self._channel.start_consuming()

    def release_resources(self):
        self._connection.close()
