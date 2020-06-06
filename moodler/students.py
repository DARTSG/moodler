import logging
import requests

from moodler.consts import REQUEST_FORMAT

logger = logging.getLogger(__name__)


class TwoStudentsFoundConflict(Exception):
    pass


def core_enrol_get_enrolled_users(course_id):
    """
    Get enrolled users by course id
    """
    response = requests.get(REQUEST_FORMAT.format('core_enrol_get_enrolled_users')
                            + '&courseid={}'.format(course_id))
    return response.json()


def get_students(course_id):
    """
    Get only the students enrolled in a course
    """
    enrolled_students = {}
    for enrolled in core_enrol_get_enrolled_users(course_id):
        if enrolled['roles'][0]['shortname'] == 'student':
            enrolled_students[enrolled['id']] = enrolled['fullname']
    return enrolled_students


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


def get_students_ids_by_names(course_id, students_names=None):
    """
    Get only the students enrolled in a course
    """
    students_ids = []

    for enrolled in core_enrol_get_enrolled_users(course_id):
        if enrolled['roles'][0]['shortname'] != 'student':
            continue

        if students_names is not None:
            if not is_student_in_names(students_names, enrolled):
                continue

        students_ids.append(enrolled['id'])

    return students_ids


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
