import requests

from moodler.consts import REQUEST_FORMAT
from moodler.students import core_course_get_contents
from moodler.submission import Submission, mod_assign_get_submissions


class InvalidAssignmentID(Exception):
    pass


class Assignment(object):
    def __init__(self, assignment_json, submissions_json, grades_json):
        self.uid = assignment_json['id']
        self.cmid = assignment_json['cmid']
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

        # Dynamic parameter used to keep track of how many ungraded submissions are in a given assignment. This may
        # change every execution.
        self.num_of_ungraded = 0

    def __repr__(self):
        return 'Assignment(id={}, name={}, submissions={})'.format(self.uid, self.name, len(self.submissions))


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


def mod_assign_get_assignments(course_id):
    """
    Returns a dictionary mapping assignment id to its name from a specified course
    """
    response = requests.get(
        REQUEST_FORMAT.format('mod_assign_get_assignments') + '&courseids[0]={}'.format(course_id))

    return response.json()["courses"][0]["assignments"]


def get_assignments(course_id, assignment_ids_to_get=None):
    """
    Retrieves assignments, grades, and submissions from server and parses into corresponding objects.

    :param course_id: The ID of the course to retrieve its assignments
    :param assignment_ids_to_get: Specific assignment IDs to retrieve.
    :return: List of Assignment() objects
    """
    all_assignment_jsons = mod_assign_get_assignments(course_id)
    assignment_ids = [assign['id'] for assign in all_assignment_jsons]

    grades = mod_assign_get_grades(assignment_ids)
    submissions = mod_assign_get_submissions(assignment_ids)
    assignments = []

    for assignment in all_assignment_jsons:
        # Filter specific assignment IDs
        if assignment_ids_to_get and assignment['cmid'] not in assignment_ids_to_get:
            continue

        assignments.append(Assignment(assignment, submissions.get(assignment['id'], []), grades.get(assignment['id'], [])))

    return assignments


def get_assignment_files(course_id, assignment_id):
    """
    Returns a list of all the file URLs for the assignment received.
    :param course_id: The ID of the course to which the assignment belongs.
    :param assignment_id: The ID of the assignment to retrieve its files.
    :return: List of all the files related to this assignment.
    """
    assignment_files = []

    # Retrieve only the files for this specific assignment ID
    assignment = get_assignments(course_id, [assignment_id])
    if assignment is None:
        raise InvalidAssignmentID()

    for attachment in assignment[0]['introattachments']:
        assignment_files.append(attachment['fileurl'])

    return assignment_files


def get_assignments_details(course_id, assignments_list):
    """
    Returns a dictionary with a tuple for every assignment name in the list
    received that looks like this: (assignment_id, assignment_section)
    :param course_id: The ID of the course to retrieve the assigments from.
    :param assignments_list: List of assignments names to retrieve their data.
    :return: Dictionary of (assignment_id, assignment_section) for every
    assignment.
    """
    # TODO: What's this function needed for? Not sure, it's unused.
    assignments_dict = {}

    # Retrieve the contents of the course
    sections = core_course_get_contents(course_id)

    # Looking through the course contents trying to locate the assignment
    for section in sections:
        for module in section['modules']:
            # We are only looking for assignments and no other resource in
            # the moodle
            if module['modname'] != 'assign':
                continue

            # Looking only for an exercise in the received list
            if module['name'] not in assignments_list:
                continue

            # Retrieve all the assignment files
            assignment_files = get_assignment_files(module['id'])

            # Adding the results to the dictionary of assignments we are
            # crafting for the caller
            assignments_dict[module['name']] = (module['id'],
                                                section['name'],
                                                assignment_files)

    return assignments_dict
