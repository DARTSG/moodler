import logging
import sys
import os
import csv

from moodler.config import STUDENTS_TO_IGNORE

logger = logging.getLogger(__name__)

ALL = 'all'
UNGRADED = 'ungraded'

BIG_NUMBER_FOR_FIELD_MAX = 0x1000000

# Indexes are by order for 'Maximum Grade', 'Grade can be changed', 'Last modified (submission)', 'Online text'
COLUMNS_TO_REMOVE = [5, 6, 7, 8]

# TODO change to DictReader so no need for this shit. Even better use pandas but fuck that
STUDENT_INDEX = 1
STATUS_INDEX = 3


class InvalidCsv(Exception):
    def __init__(self, csv_path):
        super().__init__("CSV that shouldn't be processed found at '%s'" % csv_path)


def collect_csvs(folder_path):
    """Iterate over given folder and collect target CSVs."""
    target_csvs = []
    for root, dirs, files in os.walk(folder_path):
        for _file in files:
            file_path = os.path.join(root, _file)
            if file_path.endswith('.csv') and should_modify(file_path):
                target_csvs.append(file_path)

    return target_csvs


def should_modify(csv_path):
    """
    Just a protector to make sure to not change irrelevant csv's.
    """
    # TODO: check column names
    return True


def is_resubmission(status):
    return status.endswith('- follow up submission received')


def is_student_valid(student_name):
    return student_name.strip() not in STUDENTS_TO_IGNORE.values()


def is_status_valid(status, submission_type):
    """
    Check if we want to include a row of information with the given status in our target CSV. submission_type is used to
    define more precisely which rows we want to include, and which we don't.

    :param status: Status from source CSV to check.
    :param submission_type: If submission_type is ALL, include new submissions and resubmissions. If it's UNGRADED,
    include new submissions only.
    :return: True if status should be included in target CSV, False otherwise.
    """
    # No submission - ignore
    if status.startswith('No submission'):
        return False

    # Remove submissions that are already graded
    if status.endswith('- Graded'):
        return False

    # Add entries based on the submission type defined in script
    #  and not SUB_TYPE_TO_STATUS[submissions_type](row[STATUS])
    # UNGRADED: (lambda x: 'Submitted for grading' in x and 'follow up submission received' not in x),
    if submission_type == ALL:
        return True
    elif submission_type == UNGRADED:
        if is_resubmission(status):
            return False

    # First line - just include it
    assert status.startswith('Submitted for grading') and not status.endswith('Graded')


def create_processed_path(csv_path):
    return csv_path.rsplit(".csv")[0] + "_processed.csv"


def read_csv(csv_path):
    with open(csv_path, 'rb') as source_csv:
        csv_content = source_csv.read()
        return csv_content.decode('utf-8-sig')


def handle_csv(csv_path, submission_type):
    """
    """
    submissions_counter = 0
    resubmissions_counter = 0

    # Get data
    csv_content = read_csv(csv_path)
    reader = csv.reader(csv_content.splitlines())

    # Verify document needs to be processed based on its headers
    first_row = next(reader)

    if first_row[STATUS_INDEX] != 'Status':
        raise InvalidCsv(csv_path)

    # If this is a CSV we need to process, continue to processing
    output_csv_path = create_processed_path(csv_path)
    submissions_counter, resubmissions_counter = write_output_csv(output_csv_path, submission_type, reader,
                                                                  first_row)

    # Remove original file that we read from only if we passed the first line successfully
    os.remove(csv_path)

    # Sort target file by name
    sort_csv(output_csv_path)

    return submissions_counter, resubmissions_counter


def write_output_csv(output_csv_path, submission_type, reader, first_row):
    submissions_counter = 0
    resubmissions_counter = 0

    with open(output_csv_path, 'w') as target_csv:
        writer = csv.writer(target_csv)

        row = first_row

        try:
            # Write first line from source CSV
            writer.writerow((row[0], row[1], row[2], row[3], row[4], row[9], row[10]))
        except IndexError:
            raise InvalidCsv("There has been a problem with reading the CSV "
                             "and writing it to the path: {}".format(
                                output_csv_path))

        # To prevent the following exception:
        # _csv.Error: field larger than field limit (131072)
        csv.field_size_limit(BIG_NUMBER_FOR_FIELD_MAX)

        for row in reader:
            # Verify that the submission is of the status we're looking for
            if not is_status_valid(row[STATUS_INDEX], submission_type):
                continue

            if not is_student_valid(row[STUDENT_INDEX]):
                logger.debug("Student %s made a submission, ignoring it...", row[STUDENT_INDEX])
                continue

            try:
                writer.writerow((row[0], row[1], row[2], row[3], row[4], row[9], row[10]))
            except IndexError:
                raise InvalidCsv("There has been a problem with reading the CSV"
                                 " and writing it to the path: {}".format(
                                    output_csv_path))
            if is_resubmission(row[STATUS_INDEX]):
                resubmissions_counter += 1
            else:
                submissions_counter += 1

    return submissions_counter, resubmissions_counter


def sort_csv(path):
    with open(path, 'r') as target:
        csv_input = csv.DictReader(target)
        data = sorted(csv_input, key=lambda row: (row['Full name']))

    with open(path, 'w') as target:
        csv_output = csv.DictWriter(target, fieldnames=csv_input.fieldnames)
        csv_output.writeheader()
        csv_output.writerows(data)
