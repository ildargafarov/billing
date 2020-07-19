"""
Building Flask app
"""
from flask import Flask, request

from .api_logging import logger, log
from .exceptions import BadRequest
from .billing_api import bp as billing_bp
from .responses import error_response, Statuses

ALLOWED_REQUEST_TYPES = {
    'POST'
}

ALLOWED_REQUEST_CONTENT_TYPES = {
    "application/json"
}


def check_request_content_type():
    """
    Check content-type of request
    :return: None
    """
    if (request.method in ALLOWED_REQUEST_TYPES
            and request.mimetype not in ALLOWED_REQUEST_CONTENT_TYPES):
        raise BadRequest("This content-type of request is unsupported")


def before_request():
    """
    Before each request callback
    """
    check_request_content_type()


def after_request(response):
    """
    After each request callback
    :param response: Flask Response object
    :return: Flask Response object
    """
    log(response)
    return response


def create_app(before_first_request=None, teardown_appcontext=None):
    """
    Build Flask app object
    :param before_first_request: Before first request callback
    :param teardown_appcontext: Teardown app callback
    :return: Flask app object
    """
    flask_app = Flask(__name__)

    @flask_app.route('/api/v1/billing/healthz')
    def healthz():
        return {'status': 'ok'}, 200

    @flask_app.errorhandler(BadRequest)
    def _handle_bad_request(ex):
        return (error_response(str(ex)),
                Statuses.BAD_REQUEST)

    @flask_app.errorhandler(Exception)
    def _handle_error(ex):
        logger.exception("Unexpected exception")
        return (error_response(str(ex)),
                Statuses.INTERNAL_ERROR)

    flask_app.before_request(before_request)
    flask_app.after_request(after_request)

    if before_first_request:
        flask_app.before_first_request(before_first_request)

    if teardown_appcontext:
        flask_app.teardown_appcontext(teardown_appcontext)

    flask_app.register_blueprint(billing_bp)

    return flask_app
