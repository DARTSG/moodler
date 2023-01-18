"""
This file should contain general logic for every Moodle API call.
"""
import logging

import requests

from moodler.consts import REQUEST_FORMAT
from moodler.moodle_exception import MoodlerException
from moodler.urlencode import urlencode

logger = logging.getLogger(__name__)


class MoodleAPIException(MoodlerException):
    pass


def validate_response(function_name, response):
    """
    Function that validates whether the response received is a valid response or
    is it an exception.
    """
    # In some of the moodle requests a list is returned instead
    if isinstance(response, dict):
        if "exception" in response:
            raise MoodleAPIException(
                "Moodle API call for function '{}' returned "
                "an exception response with the following "
                "message: {}".format(function_name, response["message"])
            )

        warnings = response.get("warnings", [])
        if warnings:
            # Warning example:
            # User is not enrolled or does not have requested capability
            # Warnings can also be a list of dicts if the api call returns
            # multiple objects.
            # Some warnings are useless, some are critical.

            logger.debug(
                "API function '%s' returned the following warning: %s",
                function_name,
                str(warnings),
            )


def build_url(moodle_function, **kwargs):
    """
    Generic function for building a URL for Moodle API.
    """
    url = REQUEST_FORMAT.format(moodle_function)
    url += "&" + urlencode(kwargs)
    return url


def call_moodle_api(moodle_function, **kwargs):
    """
    Utility function that will wrap a Moodle function.
    """
    url = build_url(moodle_function, **kwargs)
    response = requests.get(url)

    try:
        response_json = response.json()
    except ValueError as e:
        raise ValueError(
            f"Failed calling api to url ({url}) with status code {response.status_code}\nMake sure the URL is correct"
        ) from e

    validate_response(moodle_function, response_json)

    return response_json
