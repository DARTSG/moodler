from moodler.moodle_api import call_moodle_api, MoodleAPITimeoutException
from moodler.groups import get_course_groups
from moodler.students import get_students


class GradeReportException(Exception):
    pass


def gradereport_user_get_grade_items(courseid: int):
    """
    Get the grade report of all the users by course id
    """
    try:
        gradereport = call_moodle_api("gradereport_user_get_grade_items", courseid=courseid)
    except MoodleAPITimeoutException:
        print("Timeout when fetching all grade items, trying by groups...")
        gradereport = gradereport_user_get_grade_items_by_group(courseid)

    # Validate grade report
    if "usergrades" not in gradereport or "warnings" not in gradereport:
        raise GradeReportException("Incorrect grade report format.")

    if gradereport["warnings"]:
        raise GradeReportException(gradereport["warnings"])

    return gradereport


def gradereport_user_get_grade_items_by_group(courseid: int):
    """
    Get the grade report of all the users in course id by groups
    """
    gradereport = {"usergrades": [], "warnings": []}

    group_ids = [group.group_id for group in get_course_groups(courseid)]
    for group_id in group_ids:
        print(f"Fetching gradereport for group {group_id}...")
        
        try:
            group_gradereport = call_moodle_api("gradereport_user_get_grade_items", courseid=courseid, groupid=group_id)
        except MoodleAPITimeoutException:
            print(f"Timeout when fetching grade items for group {group_id}, trying by users...")
            return gradereport_user_get_grade_items_by_user(courseid)
        
        gradereport["usergrades"].extend(group_gradereport.get("usergrades", []))
        gradereport["warnings"].extend(group_gradereport.get("warnings", []))

    return gradereport


def gradereport_user_get_grade_items_by_user(courseid: int):
    """
    Get the grade report of all the users in course id by users
    """
    gradereport = {"usergrades": [], "warnings": []}

    student_ids = list(get_students(courseid).keys())
    print(f"Fetching gradereport for {len(student_ids)} students individually...")
    for userid in student_ids:
        # TODO: Consider using threading to speed this up

        try:
            student_gradereport = call_moodle_api("gradereport_user_get_grade_items", courseid=courseid, userid=userid)
        except MoodleAPITimeoutException:
            raise GradeReportException(f"Timeout when fetching grade items for user {userid}, stopping...")

        gradereport["usergrades"].extend(student_gradereport.get("usergrades", []))
        gradereport["warnings"].extend(student_gradereport.get("warnings", []))

    return gradereport
