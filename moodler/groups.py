from moodler.moodle_api import call_moodle_api

def get_course_groups(courseid: int):
    """
    Retrieve the groups in a course
    """
    response = call_moodle_api(
        "core_group_get_course_groups",
        courseid=courseid,
    )
    return response


def get_group_users(groupids: list[int]):
    """
    Retrieve the users in the groups
    """
    response = call_moodle_api(
        "core_group_get_group_members",
        groupids=groupids,
    )
    return response
