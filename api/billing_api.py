"""
Links Endpoints
"""

from flask import Blueprint, request
from pydantic import ValidationError

import billing
from context import app_ctx
from worker import queue_name
from .exceptions import BadRequest
from .models import (CustomersModel,
                     CustomerModel,
                     AccountsModel,
                     AccountModel,
                     RegisterCustomerModel,
                     TransactionModel,
                     AccountOperationsModel)
from .responses import (Statuses,
                        success_response,
                        error_response,
                        response)

bp = Blueprint('billing_api', __name__, url_prefix='/api/v1/billing/')


def _to_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return BadRequest('Float type expected.')


@bp.errorhandler(billing.NotFound)
def _handle_not_found(ex):
    return (error_response(str(ex)),
            Statuses.NOT_FOUND)


@bp.errorhandler(billing.LackOfMoney)
def _handle_lack_of_money(ex):
    return (error_response(str(ex)),
            Statuses.BAD_REQUEST)


@bp.route('/customers', methods=['GET'])
def get_customers():
    """
    Endpoint for getting customers
    """
    customers = app_ctx.billing.get_customers()
    return response(
        CustomersModel.parse_obj([
            CustomerModel.from_orm(customer)
            for customer in customers
        ]).json(by_alias=True),
        dump=False
    )


@bp.route('/customers/<customer_id>/accounts', methods=['GET'])
def get_customer_accounts(customer_id):
    """
    Endpoint for getting customer's accounts
    """
    accounts = app_ctx.billing.get_customer_accounts(customer_id)
    return response(
        AccountsModel.parse_obj([
            AccountModel.from_orm(account)
            for account in accounts
        ]).json(by_alias=True),
        dump=False
    )


@bp.route('/customers', methods=['POST'])
def create_customer():
    """
    Endpoint for registering new customer
    """
    data = app_ctx.billing.register_customer()
    return (RegisterCustomerModel
            .from_orm(data)
            .dict(by_alias=True))


@bp.route('/txn', methods=['POST'])
def add_txn():
    """
    Endpoint for adding new transaction
    :return: domains
    """
    data = request.get_json()

    try:
        txn = TransactionModel.parse_obj(data)
    except ValidationError as err:
        raise BadRequest(str(err))

    app_ctx.process_txn.apply_async(
        args=[txn.json(by_alias=True)],
        queue=queue_name(txn))

    resp = success_response()
    return resp


@bp.route('/accounts/<account_id>/operations', methods=['GET'])
def get_operations(account_id):
    """
    Endpoint for getting operations
    """
    operations = app_ctx.billing.get_account_operations(account_id)
    return response(
        (AccountOperationsModel
         .from_orm(operations)
         .json(by_alias=True)),
        dump=False)
