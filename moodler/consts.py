from moodler.moodler.config import TOKEN, URL


REQUEST_FORMAT = '{}/webservice/rest/server.php?wstoken={}&wsfunction={}&moodlewsrestformat=json'.format(
    URL, TOKEN, '{}')
