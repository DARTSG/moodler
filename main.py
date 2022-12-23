import argparse
import logging
from pathlib import Path
from pprint import pprint

from tabulate import tabulate

from moodler.moodle import (
    export_all,
    export_feedbacks,
    status_report,
    submissions_statistics,
)
from moodler.students import get_students

logger = logging.getLogger(__name__)


def setup_logging():
    logging.basicConfig(format="%(levelname)s - %(message)s", level=logging.INFO)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.set_defaults(which="none")
    subparsers = parser.add_subparsers(dest="which", required=True)

    parser_ungraded = subparsers.add_parser(
        "ungraded", help="Prints the amount of ungraded submissions"
    )
    parser_ungraded.add_argument("course_id", type=int, help="The course id to query")
    parser_ungraded.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Prints the names of the ungraded exercises",
    )
    parser_ungraded.add_argument(
        "--download-folder",
        "-d",
        help="If specified, the ungraded exercises will be written there",
    )

    parser_feedbacks = subparsers.add_parser("feedbacks", help="Exports the feedbacks for a course")
    parser_feedbacks.add_argument("course_id", type=int, help="The course id to query")
    parser_feedbacks.add_argument("download_folder", type=str, help="The folder to export to")

    parser_export = subparsers.add_parser(
        "export", help="Exports submissions, materials, and grades for a course"
    )
    parser_export.add_argument("course_id", type=int, help="The course id to query")
    parser_export.add_argument("download_folder", type=str, help="The folder to export to")

    parser_list_students = subparsers.add_parser("list_students", help="List names of all students")
    parser_list_students.add_argument("course_id", type=int, help="The course id to query")
    parser_student_report = subparsers.add_parser(
        "student_report",
        help="Prints a pretty table containing the amount of submissions "
        "for each student and the last submission name",
    )
    parser_student_report.add_argument("course_id", type=int, help="The course id to query")

    args = parser.parse_args()
    return args, parser


def main():
    setup_logging()

    args, parser = parse_args()

    if "none" == args.which:
        parser.print_help()
    elif "ungraded" == args.which:
        submissions_status = submissions_statistics(
            args.course_id,
            is_verbose=args.verbose,
            download_folder=args.download_folder,
        )
        print("Total ungraded: {}".format(submissions_status["total_ungraded"]))
    elif args.which == "list_students":
        pprint(get_students(args.course_id))
    elif "feedbacks" == args.which:
        export_feedbacks(args.course_id, Path(args.download_folder))
    elif "export" == args.which:
        export_all(args.course_id, Path(args.download_folder))
    elif "student_report" == args.which:
        student_statuses = status_report(args.course_id)
        headers = ("Student", "Submissions", "Last Submission")
        print(tabulate(student_statuses, headers, tablefmt="pretty"))


if "__main__" == __name__:
    main()
