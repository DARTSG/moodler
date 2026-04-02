"""Tests for moodler.attendance."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from moodler.attendance import (
    Attendance,
    AttendanceException,
    StudentAttendance,
    _get_attendance_cmid_from_course,
    _get_attendance_id_from_cmid,
    _get_attendance_sessions,
    _get_course_group_mapping,
    get_attendance_report,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

TIMESTAMP = 1700000000  # 2023-11-14 22:13:20 UTC+8 (Asia/Singapore)
HUMAN_DATE = datetime.fromtimestamp(TIMESTAMP).strftime("%Y-%m-%d %H:%M:%S")

SESSION = {
    "sessdate": TIMESTAMP,
    "groupid": 10,
    "statuses": [
        {"id": 1, "description": "Present"},
        {"id": 2, "description": "Absent"},
        {"id": 3, "description": "Excused"},
    ],
    "users": [
        {"id": 100, "firstname": "Alice", "lastname": "Smith"},
        {"id": 101, "firstname": "Bob", "lastname": "Jones"},
    ],
    "attendance_log": [
        {"studentid": 100, "statusid": "1", "remarks": ""},
        {"studentid": 101, "statusid": "2", "remarks": "Sick"},
    ],
}

ALICE = StudentAttendance(
    studentid=100,
    firstname="Alice",
    lastname="Smith",
    group="Group A",
    status="Present",
    remarks="",
)

BOB = StudentAttendance(
    studentid=101,
    firstname="Bob",
    lastname="Jones",
    group="Group B",
    status="Absent",
    remarks="Sick",
)


def _make_group(group_id: int, name: str) -> MagicMock:
    group = MagicMock()
    group.group_id = group_id
    group.name = name
    return group


# ---------------------------------------------------------------------------
# Attendance.add_to_session
# ---------------------------------------------------------------------------


def test_add_to_session_creates_new_session():
    attendance = Attendance()
    attendance.add_to_session("2023-11-14", ALICE)

    assert "2023-11-14" in attendance.sessionattendances
    assert attendance.sessionattendances["2023-11-14"] == [ALICE]


def test_add_to_session_appends_to_existing_session():
    attendance = Attendance()
    attendance.add_to_session("2023-11-14", ALICE)
    attendance.add_to_session("2023-11-14", BOB)

    assert attendance.sessionattendances["2023-11-14"] == [ALICE, BOB]


def test_add_to_session_multiple_sessions():
    attendance = Attendance()
    attendance.add_to_session("2023-11-14", ALICE)
    attendance.add_to_session("2023-11-15", BOB)

    assert len(attendance.sessionattendances) == 2
    assert attendance.sessionattendances["2023-11-14"] == [ALICE]
    assert attendance.sessionattendances["2023-11-15"] == [BOB]


# ---------------------------------------------------------------------------
# Attendance.__str__
# ---------------------------------------------------------------------------


def test_str_formats_sessions_correctly():
    attendance = Attendance()
    attendance.add_to_session("2023-11-14", ALICE)
    attendance.add_to_session("2023-11-14", BOB)

    output = str(attendance)

    assert "Session 2023-11-14 - Total 2" in output
    assert "Group A: 1" in output
    assert "Group B: 1" in output


def test_str_empty_attendance():
    assert str(Attendance()) == ""


# ---------------------------------------------------------------------------
# _get_attendance_cmid_from_course
# ---------------------------------------------------------------------------

SECTIONS_ONE_ATTENDANCE = [
    {"modules": [{"modname": "attendance", "id": 42}]},
    {"modules": [{"modname": "quiz", "id": 99}]},
]

SECTIONS_NO_ATTENDANCE = [
    {"modules": [{"modname": "quiz", "id": 99}]},
]

SECTIONS_MULTIPLE_ATTENDANCE = [
    {"modules": [{"modname": "attendance", "id": 42}]},
    {"modules": [{"modname": "attendance", "id": 43}]},
]


def test_get_attendance_cmid_returns_correct_id(mocker):
    mocker.patch(
        "moodler.attendance.core_course_get_contents",
        return_value=SECTIONS_ONE_ATTENDANCE,
    )

    cmid = _get_attendance_cmid_from_course(1)

    assert cmid == 42


def test_get_attendance_cmid_raises_when_none_found(mocker):
    mocker.patch(
        "moodler.attendance.core_course_get_contents",
        return_value=SECTIONS_NO_ATTENDANCE,
    )

    with pytest.raises(AttendanceException, match="No attendance instance found"):
        _get_attendance_cmid_from_course(1)


def test_get_attendance_cmid_raises_when_multiple_found(mocker):
    mocker.patch(
        "moodler.attendance.core_course_get_contents",
        return_value=SECTIONS_MULTIPLE_ATTENDANCE,
    )

    with pytest.raises(
        AttendanceException, match="Multiple attendance instances found"
    ):
        _get_attendance_cmid_from_course(1)


# ---------------------------------------------------------------------------
# _get_attendance_id_from_cmid
# ---------------------------------------------------------------------------


def test_get_attendance_id_from_cmid(mocker):
    mocker.patch(
        "moodler.attendance.call_moodle_api",
        return_value={"cm": {"instance": 7}},
    )

    attendance_id = _get_attendance_id_from_cmid(42)

    assert attendance_id == 7


# ---------------------------------------------------------------------------
# _get_course_group_mapping
# ---------------------------------------------------------------------------


def test_get_course_group_mapping(mocker):
    mocker.patch(
        "moodler.attendance.get_course_groups",
        return_value=[_make_group(10, "Group A"), _make_group(11, "Group B")],
    )

    mapping = _get_course_group_mapping(1)

    assert mapping == {10: "Group A", 11: "Group B"}


def test_get_course_group_mapping_empty(mocker):
    mocker.patch("moodler.attendance.get_course_groups", return_value=[])

    assert _get_course_group_mapping(1) == {}


# ---------------------------------------------------------------------------
# _get_attendance_sessions
# ---------------------------------------------------------------------------


def test_get_attendance_sessions(mocker):
    mocker.patch(
        "moodler.attendance.core_course_get_contents",
        return_value=SECTIONS_ONE_ATTENDANCE,
    )
    mock_api = mocker.patch("moodler.attendance.call_moodle_api")
    # First call resolves cmid → instance id, second call fetches sessions
    mock_api.side_effect = [
        {"cm": {"instance": 7}},
        [SESSION],
    ]

    sessions = _get_attendance_sessions(1)

    assert sessions == [SESSION]


# ---------------------------------------------------------------------------
# get_attendance_report
# ---------------------------------------------------------------------------


def test_get_attendance_report_builds_attendance_object(mocker):
    mocker.patch("moodler.attendance.check_api_permissions")
    mocker.patch(
        "moodler.attendance.core_course_get_contents",
        return_value=SECTIONS_ONE_ATTENDANCE,
    )
    mock_api = mocker.patch("moodler.attendance.call_moodle_api")
    mock_api.side_effect = [
        {"cm": {"instance": 7}},
        [SESSION],
    ]
    mocker.patch(
        "moodler.attendance.get_course_groups",
        return_value=[_make_group(10, "Group A")],
    )

    report = get_attendance_report(1)

    assert isinstance(report, Attendance)
    # Session key should be converted to a human-readable date
    assert HUMAN_DATE in report.sessionattendances
    records = report.sessionattendances[HUMAN_DATE]
    assert len(records) == 2


def test_get_attendance_report_student_fields(mocker):
    mocker.patch("moodler.attendance.check_api_permissions")
    mocker.patch(
        "moodler.attendance.core_course_get_contents",
        return_value=SECTIONS_ONE_ATTENDANCE,
    )
    mock_api = mocker.patch("moodler.attendance.call_moodle_api")
    mock_api.side_effect = [
        {"cm": {"instance": 7}},
        [SESSION],
    ]
    mocker.patch(
        "moodler.attendance.get_course_groups",
        return_value=[_make_group(10, "Group A")],
    )

    report = get_attendance_report(1)
    records = report.sessionattendances[HUMAN_DATE]

    alice = next(r for r in records if r.studentid == 100)
    assert alice.firstname == "Alice"
    assert alice.lastname == "Smith"
    assert alice.status == "Present"
    assert alice.group == "Group A"
    assert alice.remarks == ""

    bob = next(r for r in records if r.studentid == 101)
    assert bob.status == "Absent"
    assert bob.remarks == "Sick"


def test_get_attendance_report_unknown_group_falls_back(mocker):
    """Sessions with a groupid not in the mapping should fall back to '-'."""
    session_no_group = {**SESSION, "groupid": 999}

    mocker.patch("moodler.attendance.check_api_permissions")
    mocker.patch(
        "moodler.attendance.core_course_get_contents",
        return_value=SECTIONS_ONE_ATTENDANCE,
    )
    mock_api = mocker.patch("moodler.attendance.call_moodle_api")
    mock_api.side_effect = [
        {"cm": {"instance": 7}},
        [session_no_group],
    ]
    mocker.patch(
        "moodler.attendance.get_course_groups",
        return_value=[_make_group(10, "Group A")],
    )

    report = get_attendance_report(1)
    records = report.sessionattendances[HUMAN_DATE]

    assert all(r.group == "-" for r in records)


def test_get_attendance_report_checks_permissions(mocker):
    mock_check = mocker.patch("moodler.attendance.check_api_permissions")
    mocker.patch(
        "moodler.attendance.core_course_get_contents",
        return_value=SECTIONS_ONE_ATTENDANCE,
    )
    mock_api = mocker.patch("moodler.attendance.call_moodle_api")
    mock_api.side_effect = [{"cm": {"instance": 7}}, [SESSION]]
    mocker.patch("moodler.attendance.get_course_groups", return_value=[])

    get_attendance_report(1)

    mock_check.assert_called_once()
