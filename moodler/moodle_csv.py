import csv
import logging
import os
from collections import OrderedDict
from typing import Sequence

from moodler.config import STUDENTS_TO_IGNORE
from moodler.moodle_exception import MoodlerException

logger = logging.getLogger(__name__)


BIG_NUMBER_FOR_FIELD_MAX = 0x1000000

REQUIRED_GRADING_SHEET_HEADERS = [
    "Identifier",
    "Full name",
    "Email address",
    "Status",
    "Grade",
    "Last modified (grade)",
    "Feedback comments",
]

STUDENT_COL_NAME = "Full name"
STATUS_COL_NAME = "Status"


class InvalidCsv(MoodlerException):
    pass


def is_resubmission(status):
    return status.endswith("- follow up submission received")


def should_skip_student(student_name):
    return student_name.strip() in STUDENTS_TO_IGNORE.values()


def should_skip_status(status: str) -> bool:
    """Check if we should skip a row according to the status"""
    # No submission - ignore
    if status.startswith("No submission"):
        return True

    # Remove submissions that are already graded
    if status.endswith("- Graded"):
        return True

    return False


def validate_headers(headers: Sequence[str]):
    """
    Validating the row contains all the rows required in a CSV downloaded from Moodle.
    """
    if not set(REQUIRED_GRADING_SHEET_HEADERS).issubset(set(headers)):
        raise ValueError(
            f"Headers mismatch. Expected {REQUIRED_GRADING_SHEET_HEADERS} to be in {headers}"
        )


def handle_csv(csv_path):
    submissions_counter = 0
    resubmissions_counter = 0

    with open(csv_path, encoding="utf-8-sig") as f:
        data = list(csv.reader(f))

    output_csv_path = csv_path.replace(".csv", "_processed.csv")

    try:
        submissions_counter, resubmissions_counter = write_output_csv(
            output_csv_path, data
        )
    except InvalidCsv as e:
        raise InvalidCsv(csv_path) from e

    # Delete file if everything went well
    os.remove(csv_path)

    # Sort target file by name
    sort_csv(output_csv_path)

    return submissions_counter, resubmissions_counter


def write_output_csv(output_csv_path: str, data: Sequence[Sequence[str]]):
    submissions_counter = 0
    resubmissions_counter = 0

    with open(output_csv_path, "w") as target_csv:
        writer = csv.writer(target_csv)

        headers, content = data[0], data[1:]

        try:
            validate_headers(headers)
        except ValueError as e:
            raise InvalidCsv("Invalid headers") from e

        cols = OrderedDict(
            [(el, headers.index(el)) for el in REQUIRED_GRADING_SHEET_HEADERS]
        )
        # Write first line from source CSV
        writer.writerow((headers[i] for i in cols.values()))

        # To prevent the following exception:
        # _csv.Error: field larger than field limit (131072)
        csv.field_size_limit(BIG_NUMBER_FOR_FIELD_MAX)

        for row in content:
            # Remove unsued rows
            row = [row[i] for i in cols.values()]

            # Verify that the submission is of the status we're looking for
            if should_skip_status(row[cols[STATUS_COL_NAME]]):
                continue

            if should_skip_student(row[cols[STUDENT_COL_NAME]]):
                logger.debug(
                    "Student %s made a submission, ignoring it...",
                    row[cols[STUDENT_COL_NAME]],
                )
                continue

            writer.writerow(row)

            if is_resubmission(row[cols[STATUS_COL_NAME]]):
                resubmissions_counter += 1
            else:
                submissions_counter += 1

    return submissions_counter, resubmissions_counter


def sort_csv(path):
    with open(path, "r") as target:
        csv_input = csv.DictReader(target)
        data = sorted(csv_input, key=lambda row: row["Full name"])

    with open(path, "w") as target:
        csv_output = csv.DictWriter(target, fieldnames=csv_input.fieldnames)
        csv_output.writeheader()
        csv_output.writerows(data)
