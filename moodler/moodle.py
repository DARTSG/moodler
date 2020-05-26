import logging

import requests

logger = logging.getLogger(__name__)


def connect_to_server(username, password):
    """
    Function to connect to the
    :param username:
    :param password:
    :return:
    """
    session = requests.Session()

    params = {
        'anchor': '',
        'logintoken': '6932c6a583c1200d303d97109e4d7fec', # TODO: Understand this field
        'username': username,
        'password': password
    }

    session.post('http://192.168.1.55/login/index.php', params=params)

    # TODO: Check if the login has succeeded

    return session
