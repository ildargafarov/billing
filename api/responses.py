"""
Status response objects
"""
import json
from enum import IntEnum

import attr
from flask import Response


class Statuses(IntEnum):
    """
    Http statuses
    """
    SUCCESS = 200
    BAD_REQUEST = 400
    NOT_FOUND = 404
    INTERNAL_ERROR = 500


@attr.s(slots=True, frozen=True)
class Status:
    """
    Base status response object
    """
    status: str = attr.ib(default='ok')


@attr.s(slots=True, frozen=True)
class Error(Status):
    """
    Error status response object
    """
    status: str = attr.ib(default='error')
    message: str = attr.ib(default=None)


def success_response():
    """
    Build success response
    :return: Success status response object
    """
    return attr.asdict(Status())


def error_response(message):
    """
    Build error response
    :return: Error status response object
    """
    return attr.asdict(Error(message=message))


def response(any_obj, headers=None, dump=True):
    if dump:
        body = json.dumps(any_obj)
    else:
        body = any_obj

    return Response(
        body,
        mimetype="application/json",
        headers=headers
    )
