import celery
import settings
from kombu import Exchange, Queue
from celery.bin import worker as celery_worker

celery_app = None
exchange = None


def _queue_name(idx):
    return f'{settings.QUEUE_NAME_PREFIX}_queue_{idx}'


def init_celery(process_txn_task):
    name = settings.QUEUE_NAME_PREFIX
    global celery_app
    celery_app = celery.Celery(
        name,
        broker=f'amqp://{settings.RABBIT_HOST}'
    )
    global exchange
    exchange = Exchange(f'{name}_exchange',
                        type='direct')
    celery_app.conf.task_default_exchange = exchange
    celery_app.conf.task_queues = (
        Queue(
            _queue_name(idx),
            exchange
        )
        for idx in range(settings.QUEUES_COUNT)
    )
    celery_app.tasks.register(process_txn_task)
    return celery_app


def queue_name(txn):
    account_id = txn.credit_account_id
    if not account_id:
        account_id = txn.debit_account_id
    queue_idx = hash(account_id) % settings.QUEUES_COUNT
    return _queue_name(queue_idx)


def run(process_txn_task):
    celery_app = init_celery(process_txn_task)
    worker_instance = celery_worker.worker(app=celery_app)
    options = {
        'loglevel': settings.LOG_LEVEL,
        'traceback': True
    }
    if settings.QUEUE_INDEX:
        options['queues'] = [_queue_name(settings.QUEUE_INDEX)]

    worker_instance.run(**options)
