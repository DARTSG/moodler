import logging
from dataclasses import dataclass
from datetime import datetime

from moodler.groups import get_course_groups
from moodler.moodle_api import call_moodle_api, check_api_permissions
from moodler.moodle_exception import MoodlerException
from moodler.sections import core_course_get_contents

logger = logging.getLogger(__name__)

# Moodle Web Service functions required to fetch attendance data.
# These are validated against the token's permissions before any API calls are made.
REQUIRED_PERMISSIONS = [
    "core_course_get_course_module",
    "mod_attendance_get_sessions",
]


class AttendanceException(MoodlerException):
    pass


@dataclass
class StudentAttendance:
    """Represents a single student's attendance record for a session."""

    studentid: int
    firstname: str
    lastname: str
    group: str  # Name of the course group the student belongs to
    status: str
    remarks: str


class Attendance:
    """
    Aggregated attendance data for a course, keyed by session date/time string.

    ``sessionattendances`` maps a human-readable date string
    (``"YYYY-MM-DD HH:MM:SS"``) to the list of student attendance records
    for that session.
    """

    sessionattendances: dict[str, list[StudentAttendance]]

    def __init__(self):
        self.sessionattendances = {}

    def __str__(self) -> str:
        """Return a human-readable summary of attendance grouped by session and group."""
        output = ""

        for session in self.sessionattendances:
            # Count attendees per group for this session
            group_count: dict[str, int] = {}
            for student in self.sessionattendances.get(session):
                if student.group not in group_count:
                    group_count[student.group] = 0
                group_count[student.group] += 1

            output += (
                f"Session {session} - Total {len(self.sessionattendances[session])}\n"
            )
            for group, count in group_count.items():
                output += f"{group}: {count}\n"
            output += "\n"

        return output

    def add_to_session(
        self, sessdate: str, student_attendance: StudentAttendance
    ) -> None:
        """Append a student attendance record to the given session.

        Args:
            sessdate: Unix timestamp string identifying the session.
            student_attendance: The student's attendance record to add.
        """
        if sessdate not in self.sessionattendances:
            self.sessionattendances[sessdate] = []
        self.sessionattendances[sessdate].append(student_attendance)


def _get_attendance_cmid_from_course(course_id: int) -> int:
    """Return the course-module ID (cmid) of the single attendance activity in a course.

    Assumes that the course only has one attendance activity, and raises an exception
    if zero or multiple are found.

    Args:
        course_id: Moodle course ID to search.

    Raises:
        AttendanceException: If no attendance activity is found, or if more than one exists.
    """
    attendance_ids = []

    sections = core_course_get_contents(course_id)

    # Walk every section and collect IDs for modules of type "attendance"
    for section in sections:
        for module in section.get("modules", []):
            if module.get("modname") == "attendance":
                attendance_ids.append(module["id"])

    if len(attendance_ids) == 0:
        raise AttendanceException(f"No attendance instance found in course {course_id}")

    if len(attendance_ids) > 1:
        raise AttendanceException(
            f"Multiple attendance instances found in course {course_id}: {attendance_ids}"
        )

    return attendance_ids[0]


def _get_attendance_id_from_cmid(cmid: int) -> int:
    """Resolve a course-module ID to its underlying attendance instance ID.

    Moodle separates the course-module record (cmid) from the activity instance
    record (instance id). This function performs that lookup.

    Args:
        cmid: The course-module ID of the attendance activity.

    Returns:
        The attendance instance ID used by ``mod_attendance_*`` API functions.
    """
    data = call_moodle_api("core_course_get_course_module", cmid=cmid)
    return data["cm"]["instance"]


def _get_course_group_mapping(course_id: int) -> dict[int, str]:
    """Return a mapping of group ID to group name for the given course.

    Args:
        course_id: Moodle course ID.

    Returns:
        Dictionary mapping ``group_id -> group_name``.
    """
    course_groups = get_course_groups(course_id)
    return {group.group_id: group.name for group in course_groups}


def _get_attendance_sessions(course_id: int) -> list[dict]:
    """Fetch all attendance sessions for a course from the Moodle API.

    Resolves the course → cmid → attendance instance ID chain before
    calling the sessions endpoint.

    Args:
        course_id: Moodle course ID.

    Returns:
        List of session dicts as returned by ``mod_attendance_get_sessions``.
    """
    attendance_cmid = _get_attendance_cmid_from_course(course_id)
    attendance_id = _get_attendance_id_from_cmid(attendance_cmid)
    return call_moodle_api("mod_attendance_get_sessions", attendanceid=attendance_id)


def get_attendance_report(course_id: int) -> Attendance:
    """Build and return a complete attendance report for a course.

    Args:
        course_id: Moodle course ID to generate the report for.

    Returns:
        An :class:`Attendance` instance containing all session records.

    Raises:
        MoodleAPIException: If required API permissions are missing or the
            course has no attendance activity.
    """
    check_api_permissions(REQUIRED_PERMISSIONS)

    sessions = _get_attendance_sessions(course_id)
    course_group_mapping = _get_course_group_mapping(course_id)

    attendance = Attendance()
    for session in sessions:
        sessdate = str(session["sessdate"])

        # Map status IDs to their display descriptions (e.g. "Present", "Absent")
        status_map = {
            str(status["id"]): status["description"] for status in session["statuses"]
        }

        # Index enrolled users by ID for O(1) lookups when processing the log
        users = {
            user["id"]: {"firstname": user["firstname"], "lastname": user["lastname"]}
            for user in session["users"]
        }

        for student_attendance in session["attendance_log"]:
            studentid = student_attendance["studentid"]
            student_attendance_obj = StudentAttendance(
                studentid=studentid,
                firstname=users[studentid]["firstname"],
                lastname=users[studentid]["lastname"],
                # Fall back to "-" when the session has no group (whole-course session)
                group=course_group_mapping.get(session["groupid"], "-"),
                status=status_map[student_attendance["statusid"]],
                remarks=student_attendance["remarks"],
            )
            attendance.add_to_session(sessdate, student_attendance_obj)

    # Replace Unix timestamp keys with human-readable date strings
    for session in attendance.sessionattendances.copy():
        human_readable_date = datetime.fromtimestamp(int(session)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        attendance.sessionattendances[human_readable_date] = (
            attendance.sessionattendances.pop(session)
        )

    return attendance
