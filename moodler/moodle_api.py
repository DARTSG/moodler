"""
This file should contain general logic for every Moodle API call.
"""
import requests

from moodler.consts import REQUEST_FORMAT


class MoodlerException(Exception):
    pass


class MoodleAPIException(MoodlerException):
    pass


def validate_response(function_name, response):
    """
    Function that validates whether the response received is a valid response or
    is it an exception.
    """
    if 'exception' in response:
        raise MoodleAPIException("Moodle API call for function '{}' returned "
                                 "an exception response with the following "
                                 "message: {}".format(function_name,
                                                      response['message']))


def build_url(moodle_function, **kwargs):
    """
    Generic function for building a URL for Moodle API.
    """
    url = REQUEST_FORMAT(moodle_function)

    for arg_name, arg_value in kwargs.items():
        if arg_value is None:
            continue

        if isinstance(arg_value, list):
            # Appending the list of arguments into the URL for the request
            for i, arg_value_item in enumerate(arg_value):
                url += '&{}[{}]={}'.format(arg_name, i, arg_value_item)

        else:
            # Appending the argument into the URL as a parameter.
            url += '&{}={}'.format(arg_name, arg_value)

    return url


def call_moodle_api(moodle_function, **kwargs):
    """
    Utility function that will wrap a Moodle function.
    """
    url = build_url(moodle_function, **kwargs)

    response = requests.get(url).json()

    validate_response(moodle_function, response)

    return response
