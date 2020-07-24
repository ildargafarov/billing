"""
Application starting point
"""
import logging

import fire

import api
import billing
import settings
from context import init_context, app_ctx
import worker

logging.basicConfig(level=settings.LOG_LEVEL)


def _create_billing_repo():
    return billing.BillingRepository.from_params(
        settings.PG_HOST,
        settings.PG_PORT,
        settings.PG_USER,
        settings.PG_PASSWORD,
        settings.PG_DB
    )


def _create_process_txn_task():
    billing_repository = _create_billing_repo()
    billing_service = billing.BillingService(billing_repository)
    return worker.ProcessTransaction('Main', billing_service)


def create_api_app():
    def teardown_app_context(flask_ctx):
        app_ctx._billing_repository.release_connections()

    def init_services():
        """
        Create all services
        :return: None
        """
        app_ctx._billing_repository = _create_billing_repo()
        app_ctx.billing = billing.BillingService(
            app_ctx._billing_repository)
        app_ctx.process_txn = worker.ProcessTransaction('Main', app_ctx.billing)

    def before_first_request():
        """
        Before first request callback
        """
        init_context()
        init_services()
        worker.init_celery(app_ctx.process_txn)

    app = api.create_app(
        before_first_request=before_first_request,
        teardown_appcontext=teardown_app_context
    )

    return app


def start_worker():
    process_txn_task = _create_process_txn_task()
    worker.run(process_txn_task)


def init_pg_tables():
    billing_repo = _create_billing_repo()
    billing_repo.init()


if __name__ == "__main__":
    fire.Fire()
