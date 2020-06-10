import requests
import logging

from moodler.consts import REQUEST_FORMAT
from moodler.moodle_api import call_moodle_api, validate_response

logger = logging.getLogger(__name__)


class TwoStudentsFoundConflict(Exception):
    pass


def core_enrol_get_enrolled_users(course_id):
    """
    Get enrolled users by course id
    """
    response = call_moodle_api('core_enrol_get_enrolled_users',
                               courseid=course_id)

    return response


def is_student_in_names(students_names, enrolled):
    """
    Check whether the student enrolled is in the list of names received.
    """
    for student_name in students_names:
        if student_name in enrolled['fullname']:
            logger.info("Found student '%s' for the received name '%s'",
                        enrolled['fullname'],
                        student_name)
            return True

    return False


def get_students(course_id, students_names=None):
    """
    Get only the students enrolled in a course
    """
    enrolled_students = {}
    for enrolled in core_enrol_get_enrolled_users(course_id):
        if enrolled['roles'][0]['shortname'] != 'student':
            continue

        if students_names is not None:
            if not is_student_in_names(students_names, enrolled):
                continue

        enrolled_students[enrolled['id']] = enrolled['fullname']

    return enrolled_students


def list_students():
    """
    More generic than get_students, and includes all lists enrolled in the
    system. This is kept for debugging/backward compatibility, you should work
    with get_students instead.
    """
    # TODO: This is not clear how to change this to call the call_moodle_api
    #  utility function.
    response = requests.get(
        REQUEST_FORMAT.format('core_user_get_users') +
        '&criteria[0][key]=email&criteria[0][value]=%%')

    validate_response('core_user_get_users', response.json())

    # Create users map
    users_map = {}
    for user in response.json()['users']:
        users_map[user['id']] = user['firstname'] + ' ' + user['lastname']
    return users_map


def get_user_name(user_id):
    response = call_moodle_api('core_user_get_users_by_field',
                               field='id',
                               values=[user_id])

    response_json = response[0]

    return response_json['firstname'] + ' ' + response_json['lastname']
