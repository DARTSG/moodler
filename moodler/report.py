from moodler.moodle_api import call_moodle_api


class GradeReportException(Exception):
    pass


def gradereport_user_get_grade_items(courseid: int):
    """
    Get the grade report of all the users by course id
    """
    gradereport = call_moodle_api("gradereport_user_get_grade_items", courseid=courseid)

    # Validate grade report
    if "usergrades" not in gradereport or "warnings" not in gradereport:
        raise GradeReportException("Incorrect grade report format.")

    if gradereport["warnings"]:
        raise GradeReportException(gradereport["warnings"])

    return gradereport

def gradereport_user_get_grades_table(courseid: int, userid: int) -> Dict:

    gradereport = call_moodle_api("gradereport_user_get_grades_table", courseid=courseid, userid=userid)

    if "tables" not in gradereport or not gradereport["tables"]:
        raise GradeReportException("Missing or empty 'tables' in grade report.")

    if "tabledata" not in gradereport["tables"][0]:
        raise GradeReportException("Missing 'tabledata' in first table of grade report.")

    return gradereport