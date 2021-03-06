import logging
import os
import csv
from typing import Sequence

from moodler.moodle_exception import MoodlerException
from moodler.config import STUDENTS_TO_IGNORE

logger = logging.getLogger(__name__)


BIG_NUMBER_FOR_FIELD_MAX = 0x1000000

GRADING_SHEET_VALID_HEADERS = [
    "Identifier",
    "Full name",
    "Email address",
    "Status",
    "Grade",
    "Maximum Grade",
    "Grade can be changed",
    "Last modified (submission)",
    "Online text",
    "Last modified (grade)",
    "Feedback comments",
]
COLUMNS_TO_REMOVE = [5, 6, 7, 8]

STUDENT_INDEX = 1
STATUS_INDEX = 3


class InvalidCsv(MoodlerException):
    pass


def collect_csvs(folder_path):
    """Iterate over given folder and collect target CSVs."""
    target_csvs = []
    for root, dirs, files in os.walk(folder_path):
        for _file in files:
            file_path = os.path.join(root, _file)
            if file_path.endswith(".csv") and are_headers_valid(file_path):
                target_csvs.append(file_path)

    return target_csvs


def should_modify(csv_path):
    """
    Just a protector to make sure to not change irrelevant csv's.
    """
    return True


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
    if GRADING_SHEET_VALID_HEADERS != headers:
        raise ValueError(
            f"Headers mismatch. Expected {GRADING_SHEET_VALID_HEADERS}, received {headers}"
        )


def handle_csv(csv_path):
    submissions_counter = 0
    resubmissions_counter = 0

    with open(csv_path, encoding="utf-8-sig") as f:
        data = list(csv.reader(f))

    output_csv_path = csv_path.replace(".csv", "_processed.csv")

    try:
        submissions_counter, resubmissions_counter = write_output_csv(output_csv_path, data)
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

        # Write first line from source CSV
        writer.writerow((*headers[:5], *headers[-2:]))

        # To prevent the following exception:
        # _csv.Error: field larger than field limit (131072)
        csv.field_size_limit(BIG_NUMBER_FOR_FIELD_MAX)

        for row in content:
            # Remove unsued rows
            row = (*row[:5], *row[-2:])

            # Verify that the submission is of the status we're looking for
            if should_skip_status(row[STATUS_INDEX]):
                continue

            if should_skip_student(row[STUDENT_INDEX]):
                logger.debug("Student %s made a submission, ignoring it...", row[STUDENT_INDEX])
                continue

            writer.writerow(row)

            if is_resubmission(row[STATUS_INDEX]):
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
