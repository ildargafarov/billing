"""
Application starting point
"""
import fire

import api
import billing
import txn_queue
import settings
from context import init_context, app_ctx


def _create_queue_client():
    return txn_queue.rabbitmq_client(settings.RABBIT_HOST)


def _create_billing_repo():
    return billing.BillingRepository.from_params(
        settings.PG_HOST,
        settings.PG_PORT,
        settings.PG_USER,
        settings.PG_PASSWORD,
        settings.PG_DB
    )


def start_api():
    def teardown_app_context(flask_ctx):
        app_ctx._billing_repository.release_connections()

    def init_services():
        """
        Create all services
        :return: None
        """
        app_ctx.queue_client = _create_queue_client()
        app_ctx._billing_repository = _create_billing_repo()
        app_ctx.billing = billing.BillingService(
            app_ctx._billing_repository)

    def before_first_request():
        """
        Before first request callback
        """
        init_context()
        init_services()

    app = api.create_app(
        before_first_request=before_first_request,
        teardown_appcontext=teardown_app_context
    )
    app.run()


def init_pg_tables():
    billing_repo = _create_billing_repo()
    billing_repo.init()


if __name__ == "__main__":
    fire.Fire()
