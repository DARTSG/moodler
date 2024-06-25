from moodler.moodle_api import call_moodle_api


class Group(object):
    def __init__(self, group_json):
        self.group_id = group_json["id"]
        self.name = group_json["name"]

        self._group_json = group_json


def get_course_groups(courseid: int):
    """
    Retrieve the groups in a course
    """
    course_groups = call_moodle_api(
        "core_group_get_course_groups",
        courseid=courseid,
    )
    return [Group(course_group) for course_group in course_groups]


def get_group_users(groupids: list[int]):
    """
    Retrieve the users in the groups
    """
    response = call_moodle_api(
        "core_group_get_group_members",
        groupids=groupids,
    )
    return response


def get_user_group_map(course_id: int):
    """
    Maps the user to their groups

    {
        "User ID": ["Group Name"]
    }
    """
    groups = {
        course_group.group_id: course_group.name
        for course_group in get_course_groups(course_id)
    }

    if not groups:
        return ["null"], {}

    group_users = get_group_users(list(groups.keys()))

    mapping = {}
    for group in group_users:
        for userid in group["userids"]:
            mapping[userid] = groups[group["groupid"]]

    return mapping
