from moodler.groups import get_course_groups
from moodler.moodle_api import MoodleAPITimeoutException, call_moodle_api
from moodler.students import get_students


class GradeReportException(Exception):
    pass


def _validate(gradereport):
    if "usergrades" not in gradereport or "warnings" not in gradereport:
        raise GradeReportException("Incorrect grade report format.")

    if gradereport["warnings"]:
        raise GradeReportException(gradereport["warnings"])


def fetch_all(courseid: int):
    """
    Get the grade report by all users
    """
    print("Fetching gradereport for all users...")
    return call_moodle_api("gradereport_user_get_grade_items", courseid=courseid)


def fetch_by_group(courseid: int):
    """
    Get the grade report by groups
    """
    gradereport = {"usergrades": [], "warnings": []}

    for group in get_course_groups(courseid):
        print(f"Fetching gradereport for group {group.name}...")
        group_gradereport = call_moodle_api(
            "gradereport_user_get_grade_items",
            courseid=courseid,
            groupid=group.group_id,
        )
        gradereport["usergrades"].extend(group_gradereport.get("usergrades", []))
        gradereport["warnings"].extend(group_gradereport.get("warnings", []))

    return gradereport


def fetch_by_user(courseid: int):
    """
    Get the grade report by individual users
    """
    gradereport = {"usergrades": [], "warnings": []}

    student_ids = list(get_students(courseid).keys())
    print(f"Fetching gradereport for {len(student_ids)} students individually...")
    for userid in student_ids:
        # TODO: Consider using threading to speed this up
        student_gradereport = call_moodle_api(
            "gradereport_user_get_grade_items",
            courseid=courseid,
            userid=userid,
        )
        gradereport["usergrades"].extend(student_gradereport.get("usergrades", []))
        gradereport["warnings"].extend(student_gradereport.get("warnings", []))

    return gradereport


def gradereport_user_get_grade_items(courseid: int):
    """
    Get the grade report
    """
    strategies = [fetch_all, fetch_by_group, fetch_by_user]

    for strategy in strategies:
        try:
            gradereport = strategy(courseid)
            _validate(gradereport)
            return gradereport
        except MoodleAPITimeoutException:
            print(f"{strategy.__name__} timed out, trying next strategy...")
            continue

    raise GradeReportException("All strategies failed to fetch grade report.")
