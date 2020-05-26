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

import requests
from pathlib import Path
import urllib.request
import argparse
import csv


TOKEN = '53e2cd85d463774b6b4dc67e485ca61e'
URL = 'http://192.168.10.158'
REQUEST_FORMAT = '{}/webservice/rest/server.php?wstoken={}&wsfunction={}&moodlewsrestformat=json'.format(
    URL, TOKEN, '{}')


class SubmissionFile():
    def __init__(self, submission_file_json):
        self.url = submission_file_json['fileurl']
        self.timestamp = submission_file_json['timemodified']
        self._json_data = submission_file_json

    def __repr__(self):
        return 'SubmissionFile(url={}, timestamp={})'.format(self.url, self.timestamp)


class Grade():
    def __init__(self, grade_json):
        self.timestamp = grade_json['timemodified']
        if len(grade_json['grade']) == 0:
            self.grade = 0
        else:
            self.grade = float(grade_json['grade'])
        self._json_data = grade_json

    def __repr__(self):
        return 'Grade(grade={}, timestamp={})'.format(self.grade, self.timestamp)


class Submission():
    def __init__(self, user_id, grade_json, submission_json):
        self.user_id = user_id
        if grade_json is not None:
            self.grade = Grade(grade_json)
        else:
            self.grade = None
        self.status = submission_json['status']
        self.gradingstatus = submission_json['gradingstatus']
        self.submission_files = []
        for plugin in submission_json['plugins']:
            if 'file' != plugin['type']:
                continue
            for filearea in plugin['fileareas']:
                for f in filearea['files']:
                    self.submission_files.append(SubmissionFile(f))


    def __repr__(self):
        return 'Submission(user_id={}, status={}, gradingstatus={}, grade={}, submitted={})'.format(self.user_id, self.status, self.gradingstatus, self.grade, len(self.submission_files))


    def needs_grading(self):
        if 'submitted' == self.status:
            if 'notgraded' == self.gradingstatus:
                return True
            if self.grade is not None and self.grade.timestamp - max([sf.timestamp for sf in self.submission_files]) < 0:
                return True
        return False


class Assignment():
    def __init__(self, assignment_json, submissions_json, grades_json):
        self.uid = assignment_json['id']
        self.name = assignment_json['name']
        self.description = assignment_json['intro']
        self.attachments = [attachment['fileurl'] for attachment in assignment_json['introattachments']]

        self.submissions = []
        for submission in submissions_json:
            grade_json = None
            user_id = submission['userid']
            for grade in grades_json:
                if user_id == grade['userid']:
                    grade_json = grade
                    break
            if 'new' != submission['status']:
                self.submissions.append(Submission(user_id, grade_json, submission))

        self._assignment_json = assignment_json
        self._submissions_json = submissions_json
        self._grades_json = grades_json

    def __repr__(self):
        return 'Assignment(id={}, name={}, submissions={})'.format(self.uid, self.name, len(self.submissions))


class Feedback():
    def __init__(self, uid, name, answers_json):
        self.uid = uid
        self.name = name
        self.responses_count = answers_json['completedcount']
        self.questions = set()

        self.responses = [[] for i in range(self.responses_count)]

        for question in answers_json['itemsdata']:
            self.questions.add(question['item']['name'])
            for i, answer in enumerate(question['data']):
                self.responses[i].append(answer)

    def __repr__(self):
        return 'Feedback(uid={}, name={}, answers={})'.format(self.uid, self.name, self.responses_count)


def download_file(url, folder):
    file_name = url.split('/')[-1]
    if -1 != file_name.find('?'):
        file_name = file_name.split('?')[0]
    file_path = Path(folder) / Path(file_name)
    urllib.request.urlretrieve('{}?token={}'.format(url, TOKEN), file_path.as_posix())


def core_enrol_get_enrolled_users(course_id):
    """
    Get enrolled users by course id
    """
    response = requests.get(REQUEST_FORMAT.format('core_enrol_get_enrolled_users')
                            + '&courseid={}'.format(course_id))
    return response.json()


def students(course_id):
    """
    Get only the students enrolled in a course
    """
    enrolled_students = {}
    for enrolled in core_enrol_get_enrolled_users(course_id):
        if enrolled['roles'][0]['shortname'] == 'student':
            enrolled_students[enrolled['id']] = enrolled['fullname']
    return enrolled_students


def core_course_get_courses():
    """
    Returns a tuple of ids and course names
    """
    response = requests.get(REQUEST_FORMAT.format('core_course_get_courses'))
    return response.json()


def mod_assign_get_assignments(course_id):
    """
    Returns a dictionary mapping assignment id to its name from a specified course
    """
    response = requests.get(
        REQUEST_FORMAT.format('mod_assign_get_assignments') + '&courseids[0]={}'.format(course_id))

    return response.json()["courses"][0]["assignments"]


def core_course_get_contents(course_id):
    """
    Returns the structure of the course with all resources and topics
    """
    return requests.get(REQUEST_FORMAT.format('core_course_get_contents')
                        + '&courseid={}'.format(course_id)).json()


def mod_assign_get_submissions(assignment_ids):
    """
    Returns the submissions for the given assignments in a dict
    mapping assignment id to submissions
    {id: [..]}
    """

    url = REQUEST_FORMAT.format('mod_assign_get_submissions')
    for i, assignment_id in enumerate(assignment_ids):
        url += '&assignmentids[{}]={}'.format(i, assignment_id)
    response = requests.get(url)
    subs = {}
    for assign in response.json()['assignments']:
        subs[assign['assignmentid']] = assign['submissions']
    return subs


def mod_assign_get_grades(assignment_ids):
    """
    Returns the grades for all the assignments
    """
    url = REQUEST_FORMAT.format('mod_assign_get_grades')
    for i, assignment_id in enumerate(assignment_ids):
        url += '&assignmentids[{}]={}'.format(i, assignment_id)
    grades = {}
    response = requests.get(url).json()

    for grds in response['assignments']:
        grades[grds['assignmentid']] = grds['grades']

    return grades


def mod_feedback_get_feedbacks_by_courses(course_id):
    """
    Retrieves all feedbacks for a given course
    """
    return requests.get(REQUEST_FORMAT.format(
        'mod_feedback_get_feedbacks_by_courses') + '&courseids[0]={}'.format(course_id)
    ).json()['feedbacks']


def mod_feedback_get_analysis(feedback_id):
    """
    Retrieves the responses for the given feedback id
    """
    return requests.get(REQUEST_FORMAT.format(
        'mod_feedback_get_analysis') + '&feedbackid={}'.format(feedback_id)
    ).json()


def assignments(course_id):
    """
    Retrieves assignments, grades, and submissions from server and parses into corresponding objects
    Returns a list of Assignment() objects
    """
    assignment_jsons = mod_assign_get_assignments(course_id)
    assignment_ids = [assign['id'] for assign in assignment_jsons]

    grades = mod_assign_get_grades(assignment_ids)
    submissions = mod_assign_get_submissions(assignment_ids)
    assigns = []

    for assign in assignment_jsons:
        assigns.append(Assignment(assign, submissions.get(assign['id'], []), grades.get(assign['id'], [])))

    return assigns


def download(assignment_name, username, submission, download_folder):
    """
    Download the given submission, while creating the appropriate subfolders
    """
    # Create subfolders
    submission_folder = Path(download_folder) \
                        / Path(assignment_name) \
                        / Path(username)

    submission_folder.mkdir(parents=True, exist_ok=True)

    for sf in submission.submission_files:
        # Download the file
        download_file(sf.url, submission_folder)


def ungraded(course_id, verbose=False, download_folder=None):
    """
    Returns the amount exercises that need grading for a course
    If download_folder is set, downloads the ungraded exercises
    """
    assigns = assignments(course_id)
    users_map = students(course_id)
    amount = 0
    names = set()
    for assign in assigns:
        for submission in assign.submissions:
            if submission.needs_grading():
                names.add(assign.name)
                if download_folder is not None:
                    download(assign.name, users_map[submission.user_id], submission, download_folder)
                amount += 1

    if verbose:
        for name in names:
            print(name)

    return amount


def feedbacks(course_id):
    """
    Retrieve the feedbacks for a given course
    """
    fbs = []
    for feedback in mod_feedback_get_feedbacks_by_courses(course_id):
        answers = mod_feedback_get_analysis(feedback['id'])
        fbs.append(Feedback(feedback['id'], feedback['name'], answers))
    return fbs


def export_submissions(course_id, download_folder):
    """
    Downloads all submissions from a given course
    """
    assigns = assignments(course_id)
    users_map = students(course_id)
    for assign in assigns:
        for submission in assign.submissions:
            download(assign.name, users_map[submission.user_id], submission, download_folder)


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


def export_materials(course_id, folder):
    """
    Downloads all the materials from a course to a given folder
    """
    # Put assignments into a dict to find easily
    assigns = {assign.uid:assign for assign in assignments(course_id)}
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
    users_map = students(course_id)
    usernames = list(users_map.values())
    grades = [[] for i in usernames]
    exercise_names = []

    # Build a structure of {'exercise': {'student': grade, 'student2': grade}}
    for assign in assignments(course_id):
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


def main():
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
    parser_export.set_defaults(which='export')

    args = parser.parse_args()

    if 'none' == args.which:
        parser.print_help()
    elif 'ungraded' == args.which:
        print("Ungraded: {}".format(ungraded(args.course_id, verbose=args.verbose, download_folder=args.download_folder)))
    elif 'feedbacks' == args.which:
        export_feedbacks(args.course_id, args.download_folder)
    elif 'export' == args.which:
        export_all(args.course_id, args.download_folder)

if '__main__' == __name__:
    main()
