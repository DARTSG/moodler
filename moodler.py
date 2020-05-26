"""
Two main actions so far - prints how many ungraded exercises there are
and downloads student submissions

To use, you need to create a web service user and enroll it in the module
Follow the instructions at http://<MOODLE IP>/admin/category.php?category=webservicesettings

Add the following functions:
    mod_feedback_get_analysis
    mod_feedback_get_feedbacks_by_courses
    mod_assign_get_grades
    mod_assign_get_submissions
    mod_assign_get_assignments
    core_enrol_get_enrolled_users
    core_course_get_courses

The moodle API documentation can be found at http://192.168.10.158/admin/webservice/documentation.php

After following the instructions and enrolling the new user, edit the following variables below:
TOKEN
URL

Ooh, and use python3 to run this
and install requests package
"""
import logging
from pprint import pprint

import requests
from pathlib import Path
import urllib.request
import argparse
import csv

from moodler.assignment import get_assignments
from moodler.config import STUDENTS_TO_IGNORE
from moodler.download import download_file, download_submission
from moodler.feedbacks import feedbacks
from moodler.students import get_students, core_course_get_contents, list_students

logger = logging.getLogger(__name__)


def setup_logging():
    logging.basicConfig(format='%(levelname)s - %(message)s', level=logging.INFO)


def ungraded_submissions(course_id, is_verbose=False, download_folder=None):
    """
    Returns the amount exercises that need grading for a course.

    If download_folder is set, downloads the ungraded exercises
    """
    logger.info("Showing ungraded submissions for course %s", course_id)
    total_ungraded = 0

    assignments = get_assignments(course_id)
    users_map = get_students(course_id)
    for assignment in assignments:
        assignment.num_of_ungraded = 0
        # List of student names whose submissions were ignored
        ungraded_ignored = []
        # Count total number of submissions to this exercise
        total_submissions = 0
        for submission in assignment.submissions:
            # Track number of submissions made
            if submission.submitted:
                total_submissions += 1

            # Process ungraded submission
            if submission.needs_grading():
                # Check if it's a student to ignore
                student_id = submission.user_id
                if student_id in STUDENTS_TO_IGNORE.keys():
                    ungraded_ignored.append(STUDENTS_TO_IGNORE[student_id])
                else:
                    assignment.num_of_ungraded += 1
                # TODO: Improve with 'attemptnumber' field, to check "== 0" for new submissions only, or resubmissions

                if download_folder is not None:
                    download_submission(assignment.name, users_map[submission.user_id], submission, download_folder)

        # Print total stats about this assignment
        if is_verbose and len(ungraded_ignored) != 0:
            logger.info("Ignored %s submissions for assignment '%s' (CMID %s, ID %s): %s", len(ungraded_ignored),
                        assignment.name, assignment.cmid, assignment.uid, ungraded_ignored)
        if assignment.num_of_ungraded != 0:
            logger.info("Total ungraded for assignment '%s' (CMID %s, ID %s): %s/%s", assignment.name,
                        assignment.cmid, assignment.uid, assignment.num_of_ungraded, total_submissions)
        total_ungraded += assignment.num_of_ungraded

    return total_ungraded


def export_feedbacks(course_id, folder):
    """
    Exports the feedbacks of a course, in csv format, to a speicifed folder.
    """
    for feedback in feedbacks(course_id):
        if feedback.responses_count == 0:
            # Stop if reached a feedback that wasn't filled yet
            return
        file_path = Path(folder) / Path(feedback.name)
        with open(str(file_path) + '.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(feedback.questions)
            writer.writerows(feedback.responses)


def export_submissions(course_id, download_folder):
    """
    Downloads all submissions from a given course
    """
    assigns = get_assignments(course_id)
    users_map = get_students(course_id)
    for assign in assigns:
        for submission in assign.submissions:
            download(assign.name, users_map[submission.user_id], submission, download_folder)


def export_materials(course_id, folder):
    """
    Downloads all the materials from a course to a given folder
    """
    # Put assignments into a dict to find easily
    assigns = {assign.uid: assign for assign in get_assignments(course_id)}
    sections = core_course_get_contents(course_id)

    created = set()

    for section in sections:
        section_folder = Path(folder) / Path(section['name'])
        for module in section['modules']:
            # Create section folder
            if module['modname'] in ['feedback', 'forum']:
                continue
            elif module['modname'] == 'resource':
                if section['name'] not in created:
                    section_folder.mkdir(parents=True, exist_ok=True)
                    created.add(section['name'])
                # If module is a resource - download it
                for resource in module['contents']:
                    download_file(resource['fileurl'], section_folder)
            elif module['modname'] == 'assign':
                if section['name'] not in created:
                    section_folder.mkdir(parents=True, exist_ok=True)
                    created.add(section['name'])
                # If module is an assignment - download attachments and description
                assign = assigns[module['instance']]
                if len(assign.description) > 0:
                    description_file = section_folder / Path(assign.name).with_suffix('.txt')
                    with open(description_file, 'w') as f:
                        f.write(assign.description)
                for attachment in assign.attachments:
                    download_file(attachment, section_folder)


def export_grades(course_id, folder):
    """
    Exports the complete grade file to the given folder in csv format
    """
    users_map = get_students(course_id)
    usernames = list(users_map.values())
    grades = [[] for i in usernames]
    exercise_names = []

    # Build a structure of {'exercise': {'student': grade, 'student2': grade}}
    for assign in get_assignments(course_id):
        exercise_names.append(assign.name)
        students_not_submitted = list(usernames)
        for submission in assign.submissions:
            grades[usernames.index(users_map[submission.user_id])].append(submission.grade.grade if submission.grade else 0)
            students_not_submitted.remove(users_map[submission.user_id])
        # Just grade users that did not submit an assignment with a 0
        for student in students_not_submitted:
            grades[usernames.index(student)].append(0)

    with open(Path(folder) / 'Grades.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Student Name'] + exercise_names + ['Total'])
        for i, row in enumerate(grades):
            writer.writerow([usernames[i]] + row + [sum(row)])


def export_all(course_id, folder):
    """
    Exports submissions, materials, and grades for the given course
    """
    export_grades(course_id, folder)
    export_materials(course_id, Path(folder) / 'Materials')
    export_submissions(course_id, Path(folder) / 'Submissions')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.set_defaults(which='none')
    subparsers = parser.add_subparsers()

    parser_ungraded = subparsers.add_parser('ungraded',
                                            help='Prints the amount of ungraded submissions')
    parser_ungraded.add_argument('course_id', type=int, help='The course id to query')
    parser_ungraded.add_argument('--verbose', '-v', action='store_true',
                                 help='Prints the names of the ungraded exercises')
    parser_ungraded.add_argument('--download-folder', '-d',
                                 help='If specified, the ungraded exercises will be written there')
    parser_ungraded.set_defaults(which='ungraded')

    parser_feedbacks = subparsers.add_parser('feedbacks',
                                             help='Exports the feedbacks for a course')
    parser_feedbacks.add_argument('course_id', type=int, help='The course id to query')
    parser_feedbacks.add_argument('download_folder', type=str,
                                  help='The folder to export to')
    parser_feedbacks.set_defaults(which='feedbacks')

    parser_export = subparsers.add_parser('export',
                                             help='Exports submissions, materials, and grades for a course')
    parser_export.add_argument('course_id', type=int, help='The course id to query')
    parser_export.add_argument('download_folder', type=str,
                                  help='The folder to export to')

    parser_list_students = subparsers.add_parser('list_students',
                                                 help='List names of all students')
    parser_list_students.add_argument('course_id', type=int, help='The course id to query')
    parser_list_students.set_defaults(which='list_students')
    # parser_export.set_defaults(which='export')

    args = parser.parse_args()
    return args, parser


def main():
    setup_logging()

    args, parser = parse_args()

    if 'none' == args.which:
        parser.print_help()
    elif 'ungraded' == args.which:
        print("Ungraded: {}".format(ungraded_submissions(args.course_id, is_verbose=args.verbose, download_folder=args.download_folder)))
    elif args.which == 'list_students':
        pprint(get_students(args.course_id))
    elif 'feedbacks' == args.which:
        export_feedbacks(args.course_id, args.download_folder)
    elif 'export' == args.which:
        export_all(args.course_id, args.download_folder)


if '__main__' == __name__:
    main()
