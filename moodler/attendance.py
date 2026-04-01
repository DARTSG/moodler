import logging
from dataclasses import dataclass
from typing import Literal
from datetime import datetime

from moodler.groups import get_course_groups
from moodler.moodle_api import call_moodle_api, check_api_permissions
from moodler.moodle_exception import MoodlerException
from moodler.sections import core_course_get_contents

logger = logging.getLogger(__name__)

REQUIRED_PERMISSIONS = [
    "core_course_get_course_module",
    "mod_attendance_get_sessions",
]


class AttendanceException(MoodlerException):
    pass


@dataclass
class StudentAttendance:
    studentid: int
    firstname: str
    lastname: str
    group: str
    status: Literal["Present", "Absent", "Excused"]
    remarks: str


class Attendance:
    sessionattendances: dict[str, list[StudentAttendance]]

    def __init__(self):
        self.sessionattendances = {}

    def __str__(self) -> str:
        output = ""

        for session in self.sessionattendances:
            group_count = {}
            for student in self.sessionattendances.get(session):
                if student.group not in group_count:
                    group_count[student.group] = 0
                group_count[student.group] += 1

            output += (
                f"Session {session} - Total {len(self.sessionattendances[session])}\n"
            )
            for i in group_count:
                output += f"{i}: {group_count[i]}\n"
            output += "\n"

        return output

    def add_to_session(
        self, sessdate: str, student_attendance: StudentAttendance
    ) -> None:
        if sessdate not in self.sessionattendances:
            self.sessionattendances[sessdate] = []
        self.sessionattendances[sessdate].append(student_attendance)


def _get_attendance_id_from_course(course_id: int) -> int | None:
    attendance_ids = []

    sections = core_course_get_contents(course_id)

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
    data = call_moodle_api("core_course_get_course_module", cmid=cmid)
    return data["cm"]["instance"]


def _get_course_group_mapping(course_id: int) -> dict[int, str]:
    course_groups = get_course_groups(course_id)
    return {group.group_id: group.name for group in course_groups}


def _get_attendance_sessions(course_id: int) -> list[dict]:
    attendance_cmid = _get_attendance_id_from_course(course_id)
    attendance_id = _get_attendance_id_from_cmid(attendance_cmid)
    return call_moodle_api("mod_attendance_get_sessions", attendanceid=attendance_id)


def get_attendance_report(course_id: int) -> Attendance | None:
    check_api_permissions(REQUIRED_PERMISSIONS)

    sessions = _get_attendance_sessions(course_id)
    course_group_mapping = _get_course_group_mapping(course_id)

    attendance = Attendance()
    for session in sessions:
        sessdate = str(session["sessdate"])
        status_map = {
            str(status["id"]): status["description"] for status in session["statuses"]
        }
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
                group=course_group_mapping.get(session["groupid"], "-"),
                status=status_map[student_attendance["statusid"]],
                remarks=student_attendance["remarks"],
            )
            attendance.add_to_session(sessdate, student_attendance_obj)

    for session in attendance.sessionattendances.copy():
        human_readable_date = datetime.fromtimestamp(int(session)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        attendance.sessionattendances[
            human_readable_date
        ] = attendance.sessionattendances.pop(session)

    return attendance
