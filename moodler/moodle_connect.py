"""
This file contains only the logic for connecting to the website and creating
a session object. The thing is this logic must be separate from the moodle
logic since we don't want the __init__ to import the moodle module and then
the moodle module will import the __init__ and we will have a circle of
imports.

So this file is meant only for containing the login logics. It will calculate
and connect to the moodle to create a session cookie that will be used to run
API directly from the web interface.
"""
import re
import requests

from moodler.config import URL, LOGIN_PAGE


LOGIN_TOKEN_PATTERN = r'name="logintoken" value="([\w\d]+)"'
FAILED_LOGIN_PATTERN = r'Invalid login'


class LoginTokenNotFound(Exception):
    pass


class InvalidUsernameOrPassword(Exception):
    pass


def connect_to_server(username, password):
    """
    Function to connect to the server.
    :param username: The username to use in the connection to the server.
    :param password: The password to use in the connection to the server.
    :return: A session object of the new session created for the connection
    of the used username and password.
    """
    session = requests.Session()

    # Using this get request in order to retrieve the login token for the
    # login request.
    login_page_response = session.get('{}/{}'.format(URL, LOGIN_PAGE))

    # Looking for the login token within the login page using regex.
    login_token_match = re.search(LOGIN_TOKEN_PATTERN,
                                  login_page_response.content.decode())
    if login_token_match is None:
        raise LoginTokenNotFound()

    login_token = login_token_match.group(1)

    # Using the login token we have found within the login page to create the
    # parameters for the real login.
    params = {
        'anchor': '',
        'logintoken': login_token,
        'username': username,
        'password': password
    }

    # Sending the login request.
    login_post_response = session.post('{}/{}'.format(URL, LOGIN_PAGE),
                                       data=params)

    # Check if the login has failed due to invalid credentials
    failed_login_match = re.search(FAILED_LOGIN_PATTERN,
                                   login_post_response.content.decode())
    # If the search has succeeded and in the response we have found an
    # indicator for failed login, then we should raise an exception.
    if failed_login_match is not None:
        raise InvalidUsernameOrPassword()

    return session
