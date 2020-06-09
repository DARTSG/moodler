from moodler.config import TOKEN, URL


REQUEST_FORMAT = '{}/webservice/rest/server.php?wstoken={}&wsfunction={}&moodlewsrestformat=json'.format(
    URL, TOKEN, '{}')


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
