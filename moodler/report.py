from moodler.moodle_api import call_moodle_api


def gradereport_user_get_grade_items(courseid: int):
    """
    Get the grade report of all the users by course id
    """
    response = call_moodle_api("gradereport_user_get_grade_items", courseid=courseid)
    return response
