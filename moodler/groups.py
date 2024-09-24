from typing import Any, Dict, List

from moodler.moodle_api import call_moodle_api
from moodler.students import get_students


class Group(object):
    def __init__(self, group_json: Dict[str, Any]):
        self.group_id: int = group_json["id"]
        self.name: str = group_json["name"]

        self._group_json: Dict[str, Any] = group_json


def get_course_groups(courseid: int) -> List[Group]:
    """
    Retrieve the groups in a course
    """
    course_groups = call_moodle_api(
        "core_group_get_course_groups",
        courseid=courseid,
    )
    return [Group(course_group) for course_group in course_groups]


def get_group_users(groupids: List[int]) -> List[Dict[str, Any]]:
    """
    Retrieve the users in the groups

    Response:
    [
        {"groupid": 1, "userids": [1, 2]},
    ]
    """
    response = call_moodle_api(
        "core_group_get_group_members",
        groupids=groupids,
    )
    return response


def get_user_group_map(course_id: int) -> Dict[str, List[str]]:
    """
    Maps the user to their groups, returns an empty dictionary if there are no
    groups in the course

    {
        "User ID": ["Group Name"]
    }
    """
    groups = {
        course_group.group_id: course_group.name
        for course_group in get_course_groups(course_id)
    }

    if not groups:
        return {}

    group_users = get_group_users(list(groups.keys()))

    mapping = {}
    for group in group_users:
        for userid in group["userids"]:
            mapping[userid] = groups[group["groupid"]]

    return mapping


def get_student_map(course_id: int):
    """
    Retrieve all students name and group in the course

    Example Output:
    {
        1: {
            "name": "Student 1",
            "group": "Group 1",
        },
        2: {
            "name": "Student 2",
            "group": "Group 2",
        },
    }
    """
    students = get_students(course_id)
    group_map = get_user_group_map(course_id)

    return {
        id: {
            "name": name,
            "group": "" if not group_map else group_map[id],
        }
        for id, name in students.items()
    }
