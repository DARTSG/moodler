import requests

from moodler.consts import REQUEST_FORMAT


def core_enrol_get_enrolled_users(course_id):
    """
    Get enrolled users by course id
    """
    response = requests.get(REQUEST_FORMAT.format('core_enrol_get_enrolled_users')
                            + '&courseid={}'.format(course_id))
    return response.json()


def core_course_get_courses():
    """
    Returns a tuple of ids and course names
    """
    response = requests.get(REQUEST_FORMAT.format('core_course_get_courses'))
    return response.json()


def core_course_get_contents(course_id):
    """
    Returns the structure of the course with all resources and topics
    """
    return requests.get(REQUEST_FORMAT.format('core_course_get_contents')
                        + '&courseid={}'.format(course_id)).json()


def get_students(course_id):
    """
    Get only the students enrolled in a course
    """
    enrolled_students = {}
    for enrolled in core_enrol_get_enrolled_users(course_id):
        if enrolled['roles'][0]['shortname'] == 'student':
            enrolled_students[enrolled['id']] = enrolled['fullname']
    return enrolled_students


def list_students():
    """
    More generic than get_students, and includes all lists enrolled in the system. This is kept for debugging/backward
    compatibility, you should work with get_students instead.
    """
    response = requests.get(
        REQUEST_FORMAT.format('core_user_get_users') + '&criteria[0][key]=email&criteria[0][value]=%%')

    # Create users map
    users_map = {}
    for user in response.json()['users']:
        users_map[user['id']] = user['firstname'] + ' ' + user['lastname']
    return users_map


def get_user_name(user_id):
    response = requests.get(
        REQUEST_FORMAT.format('core_user_get_users_by_field') + '&field=id&values[0]={}'.format(user_id))
    response_json = response.json()[0]
    return response_json['firstname'] + ' ' + response_json['lastname']
