import os
import csv
from datetime import datetime
from pathlib import Path

import pytest

from moodler.moodle_csv import (
    has_grade,
    is_empty_field,
    is_resubmission,
    parse_datetime,
    should_skip_status,
    write_output_csv,
)

TESTDATA_DIR = Path(__file__).parent / "test_data"
os.environ["LTI_TOKEN"] = ""
os.environ["LTI_URL"] = ""


@pytest.mark.parametrize(
    "input,expected",
    (
        ("", True),
        (" ", True),
        ("-", True),
        (" - ", True),
        ("0", False),
        ("1", False),
    ),
)
def test_is_empty_field(input, expected):
    assert is_empty_field(input) == expected


@pytest.mark.parametrize(
    "input,expected",
    (
        ("", False),
        ("0.00", True),
        ("1", True),
        ("100", True),
        ("100.0", True),
        ("-1.00", False),
        ("Invalid value should return False", False),
    ),
)
def test_has_grade(input, expected):
    assert has_grade(input) == expected


@pytest.mark.parametrize(
    "input,expected",
    (
        ("Thursday, 9 February 2023, 8:52 AM", datetime(2023, 2, 9, 8, 52)),
        ("Thursday, 9 February 2023, 8:52 PM", datetime(2023, 2, 9, 20, 52)),
        ("Sunday, 19 March 2023, 12:00 AM", datetime(2023, 3, 19, 0, 0)),
    ),
)
def test_parse_datetime(input, expected):
    assert parse_datetime(input) == expected


def test_parse_datetime_invalid():
    with pytest.raises(ValueError):
        parse_datetime("Thursday, 9 February 2023, 8:52")


@pytest.mark.parametrize(
    "status,last_modified_grade,last_modified_sub,expected",
    (
        ("Submitted", "", "", False),
        ("No submission", "-", "-", False),
        ("Submitted", "Thursday, 9 February 2023, 8:52 AM", "", False),
        ("Submitted", "", "Thursday, 9 February 2023, 8:52 AM", False),
        (
            "Submitted",
            "Thursday, 9 February 2023, 8:51 AM",
            "Thursday, 9 February 2023, 8:52 AM",
            True,
        ),
        (
            "Submitted",
            "Thursday, 9 February 2023, 8:52 AM",
            "Thursday, 9 February 2023, 8:51 AM",
            False,
        ),
        (
            "Submitted",
            "Thursday, 9 February 2023, 8:52 AM",
            "Thursday, 9 February 2023, 8:52 AM",
            True,
        ),
        ("Submitted - follow up submission received", "", "", True),
        (
            "Submitted - follow up submission received",
            "Thursday, 9 February 2023, 8:52 AM",
            "",
            True,
        ),
        (
            "Submitted - follow up submission received",
            "",
            "Thursday, 9 February 2023, 8:52 AM",
            True,
        ),
        (
            "Submitted - follow up submission received",
            "Thursday, 9 February 2023, 8:52 AM",
            "Thursday, 9 February 2023, 8:52 AM",
            True,
        ),
    ),
)
def test_is_resubmission(status, last_modified_grade, last_modified_sub, expected):
    assert is_resubmission(status, last_modified_grade, last_modified_sub) == expected


@pytest.mark.parametrize(
    "status,expected",
    (
        ("No submission", True),
        ("Submitted - follow up submission received", False),
        ("Submitted - Graded", True),
        ("Submitted - Graded - follow up submission received", False),
    ),
)
def test_should_skip_status(status, expected):
    assert should_skip_status(status) == expected


@pytest.mark.parametrize(
    "input_csv,expected_csv",
    (
        (
            TESTDATA_DIR / "marking_grade_worksheet_input.csv",
            TESTDATA_DIR / "marking_grade_worksheet_output.csv",
        ),
        (
            TESTDATA_DIR / "grade_worksheet_input.csv",
            TESTDATA_DIR / "grade_worksheet_output.csv",
        ),
        (
            TESTDATA_DIR / "python_input.csv",
            TESTDATA_DIR / "python_output.csv",
        ),
    ),
)
def test_write_output_csv(tmp_path, input_csv, expected_csv):
    output_csv = tmp_path / "output.csv"
    data = list(csv.reader(input_csv.open("r")))
    write_output_csv(output_csv, data)
    assert output_csv.read_text() == expected_csv.read_text()
