import logging

from moodler.moodle_api import MoodleAPIException, call_moodle_api
from moodler.moodle_exception import MoodlerException

logger = logging.getLogger(__name__)


class TwoStudentsFoundConflict(MoodlerException):
    pass


def core_enrol_get_enrolled_users(course_id):
    """
    Get enrolled users by course id, returns a list of enrolled users
    """
    response = call_moodle_api(
        "core_enrol_get_enrolled_users", courseid=course_id
    )
    if not isinstance(response, list):
        raise MoodleAPIException(
            "core_enrol_get_enrolled_users does not return a list."
        )
    return response


def get_students_ids_by_name(course_id, students_names: list):
    """
    The function is locating students IDs according to their name. The function
    receives a list of names to search in the enrolled students of the course
    and will try to locate these students in the course. It will return the
    IDs of all of the students it has found.
    :param course_id: The ID of the course in which to locate the students.
    :param students_names: The list of students to search in the course.
    """
    students_names_to_ids_dict = {}

    for student_name in students_names:
        for enrolled in core_enrol_get_enrolled_users(course_id):
            if enrolled["roles"][0]["shortname"] != "student":
                continue

            # Trying to locate a student that has a similar name to one of
            # the names received in the input list.
            if student_name.lower() not in enrolled["fullname"].lower():
                continue

            # At this point, we have found a student in the course that has a
            # similar name to one of the names in the input list students_names
            logger.info(
                "Found student '%s' for the received name '%s'",
                enrolled["fullname"],
                student_name,
            )

            if student_name not in students_names_to_ids_dict:
                students_names_to_ids_dict[student_name] = enrolled["id"]

            # If we have already found this student in the course, that means
            # that the specified name in the list is not specific enough and
            # fits more than one names in the course.
            # We do not want duplications!
            else:
                logger.error(
                    "Found more than one student containing this name. You should be more indicative with the name you specify. "
                    "For example, if you specify 'Tan', it is not indicative enough to understand who you are talking about since it is a very common surname!"
                )
                del students_names_to_ids_dict[student_name]

    return list(students_names_to_ids_dict.values())


def get_students(course_id):
    """
    Get only the students enrolled in a course
    """
    output_enrolled_students: dict[int, str] = {}

    for enrolled in core_enrol_get_enrolled_users(course_id):
        if enrolled["roles"][0]["shortname"] != "student":
            continue

        output_enrolled_students[enrolled["id"]] = enrolled["fullname"]

    return output_enrolled_students


def list_students():
    """
    More generic than get_students, and includes all lists enrolled in the
    system. This is kept for debugging/backward compatibility, you should work
    with get_students instead.
    """
    response = call_moodle_api(
        "core_user_get_users", criteria=[{"key": "email", "value": "%%"}]
    )
    # Create users map
    users_map = {}
    for user in response.json()["users"]:
        users_map[user["id"]] = user["firstname"] + " " + user["lastname"]
    return users_map


def get_user_name(user_id):
    response = call_moodle_api(
        "core_user_get_users_by_field", field="id", values=[user_id]
    )

    response_json = response[0]

    return response_json["firstname"] + " " + response_json["lastname"]


def get_students_raw(courseid: int):
    """
    Get the raw data of students in the course
    """
    students = [
        user
        for user in core_enrol_get_enrolled_users(courseid)
        if any(role.get("shortname") == "student" for role in user["roles"])
    ]
    return students
