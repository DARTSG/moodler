"""
This file should contain general logic for every Moodle API call.
"""
import logging

import requests

from moodler.consts import TOKEN, URL
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


def prepare_data(moodle_function, **kwargs):
    """
    Generic function for building urlencoded data for Moodle API.
    """
    return urlencode(
        {
            **kwargs,
            "wstoken": TOKEN,
            "wsfunction": moodle_function,
            "moodlewsrestformat": "json",
        }
    )


def call_moodle_api(moodle_function, **kwargs):
    """
    Utility function that will wrap a Moodle function.
    """
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = prepare_data(moodle_function, **kwargs)
    response = requests.post(URL, data, headers=headers)
    response.raise_for_status()
    try:
        response_json = response.json()
    except ValueError as e:
        raise ValueError(
            f"Failed calling api with the data ({data}) with status code "
            f"{response.status_code}\nMake sure the URL is correct"
        ) from e

    validate_response(moodle_function, response_json)
    return response_json
