import celery
import settings
from celery.bin import worker as celery_worker

celery_app = None


def init_celery(name, process_txn_task):
    global celery_app
    celery_app = celery.Celery(
        name,
        broker=f'amqp://{settings.RABBIT_HOST}'
    )
    celery_app.tasks.register(process_txn_task)
    return celery_app


def run(process_txn_task):
    celery_app = init_celery(settings.WORKER_NAME_PREFIX, process_txn_task)
    worker_instance = celery_worker.worker(app=celery_app)
    options = {
        'loglevel': settings.LOG_LEVEL,
        'traceback': True
    }

    worker_instance.run(**options)
