"""
Links Endpoints
"""
from flask import Blueprint, request

from context import app_ctx
from .exceptions import BadRequest
from .responses import (Statuses,
                        success_response,
                        error_response,
                        response)
import txn_queue
import billing

bp = Blueprint('billing_api', __name__, url_prefix='/api/v1/billing/')


@bp.errorhandler(billing.NotFound)
def _handle_not_found(ex):
    return (error_response(str(ex)),
            Statuses.NOT_FOUND)


@bp.route('/customers', methods=['GET'])
def get_customers():
    """
    Endpoint for getting customers
    """
    customers = app_ctx.billing.get_customers()
    return response([
        {
            "id": customer.id,
            "registerDate": customer.register_date.isoformat()
        }
        for customer in customers
    ])


@bp.route('/customers/<customer_id>/accounts', methods=['GET'])
def get_customer_accounts(customer_id):
    """
    Endpoint for getting customer's accounts
    """
    accounts = app_ctx.billing.get_customer_accounts(customer_id)
    return response([
        {
            "customerId": account.customer_id,
            "id": account.id,
            "balance": float(account.balance),
            "createDate": account.create_date.isoformat()
        }
        for account in accounts
    ])


@bp.route('/customers', methods=['POST'])
def create_customer():
    """
    Endpoint for registering new customer
    """
    data = app_ctx.billing.register_customer()
    return {
        "customerId": data.customer_id,
        "accountId": data.current_account_id
    }


@bp.route('/txn', methods=['POST'])
def add_txn():
    """
    Endpoint for adding new transaction
    :return: domains
    """
    data = request.get_json()
    if not data.get('debit_account_id'):
        raise BadRequest('Field "debit_account_id" is required')
    if not data.get('amount'):
        raise BadRequest('Field "amount" is required')

    txn = txn_queue.Transaction.from_data(
        data.get('amount'),
        data.get('credit_account_id'),
        data.get('debit_account_id')
    )
    domains = app_ctx.queue_client.add(txn)

    resp = success_response()
    resp['domains'] = list(domains.domains)
    return resp
