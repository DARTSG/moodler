import logging
import requests

from moodler.config import URL
from moodler.consts import REQUEST_FORMAT, validate_response
from moodler.students import get_user_name, get_students_ids_by_names
from moodler.submission import Submission, mod_assign_get_submissions, MissingGrade

logger = logging.getLogger(__name__)


class InvalidAssignmentID(Exception):
    pass


class Assignment(object):
    def __init__(self, assignment_json, submissions_json, grades_json):
        # a random number Moodle generates in API (not seen when you use Moodle visually)
        self.uid = assignment_json['id']
        # the actual ID that you see in the Moodle interface
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
                try:
                    self.submissions.append(Submission(user_id, grade_json, submission))
                except MissingGrade:
                    logger.warning("Missing grade for student \"{}\" in assignment \"{}\". Fix ASAP at {}".format(
                        get_user_name(user_id),
                        self.name,
                        "{}//mod/assign/view.php?id={}&action=grader&userid={}".format(URL, self.cmid, user_id)))
                    self.submissions.append(Submission(user_id, None, submission))

        self._assignment_json = assignment_json
        self._submissions_json = submissions_json
        self._grades_json = grades_json

        # Dynamic parameter used to keep track of how many ungraded submissions are in a given assignment. This may
        # change every execution.
        self.num_of_ungraded = 0

    def ungraded(self):
        submissions = []
        for submission in self.submissions:
            # Process ungraded submission
            if submission.needs_grading():
                submissions.append(submission)
        return submissions

    def __repr__(self):
        return 'Assignment(id={}, name={}, submissions={})'.format(self.uid, self.name, len(self.submissions))

    def lock_submissions(self, course_id, students=None):
        """
        Locking submissions for this specific assignment.
        """
        students_ids = get_students_ids_by_names(course_id, students)
        mod_assign_lock_submissions(self.cmid, students_ids)

        logger.info("Locked submissions for assignment '%s' for %s",
                    self.name,
                    students if students is not None else "all students.")

    def unlock_submissions(self, course_id, students=None):
        """
        Locking submissions for this specific assignment.
        """
        students_ids = get_students_ids_by_names(course_id, students)
        mod_assign_unlock_submissions(self.cmid, students_ids)

        logger.info("Locked submissions for assignment '%s' for %s",
                    self.name,
                    students if students is not None else "all students.")


def mod_assign_lock_submissions(assignment_id, user_ids):
    """
    Locks submissions for a specific assignments for a specific user(s).
    """
    params = {
        'assignmentid': assignment_id,
        'userids': user_ids
    }
    response = requests.get(
        REQUEST_FORMAT.format('mod_assign_lock_submissions'),
        params=params)

    validate_response('mod_assign_lock_submissions', response.json())


def mod_assign_unlock_submissions(assignment_id, user_ids):
    """
    Unlocks submissions for a specific assignments for a specific user(s).
    """
    params = {
        'assignmentid': assignment_id,
        'userids': user_ids
    }
    response = requests.get(
        REQUEST_FORMAT.format('mod_assign_unlock_submissions'),
        params=params)

    validate_response('mod_assign_unlock_submissions', response.json())


def mod_assign_get_grades(assignment_ids):
    """
    Returns the grades for all the assignments
    """
    url = REQUEST_FORMAT.format('mod_assign_get_grades')
    for i, assignment_id in enumerate(assignment_ids):
        url += '&assignmentids[{}]={}'.format(i, assignment_id)
    grades = {}
    response = requests.get(url).json()

    validate_response('mod_assign_get_grades', response.json())

    for grds in response['assignments']:
        grades[grds['assignmentid']] = grds['grades']

    return grades


def mod_assign_get_assignments(course_id):
    """
    Returns a dictionary mapping assignment id to its name from a specified course
    """
    response = requests.get(
        REQUEST_FORMAT.format('mod_assign_get_assignments') + '&courseids[0]={}'.format(course_id))

    validate_response('mod_assign_get_assignments', response.json())

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

    assignments_not_found = None
    if assignment_ids_to_get:
        assignments_not_found = assignment_ids_to_get[:]

    for assignment in all_assignment_jsons:
        # Filter specific assignment IDs
        if assignment_ids_to_get and assignment['cmid'] not in assignment_ids_to_get:
            continue

        assignments.append(Assignment(assignment,
                                      submissions.get(assignment['id'], []),
                                      grades.get(assignment['id'], [])))

        if assignments_not_found is not None:
            assignments_not_found.remove(assignment['cmid'])

    if assignments_not_found:
        logger.error("Could not find the following exercises for the trainer: "
                     "%s", assignments_not_found)

    return assignments


def get_assignments_by_names(course_id, assignment_names_to_get=None):
    """
    Retrieves assignments, grades, and submissions from server and parses into corresponding objects.

    :param course_id: The ID of the course to retrieve its assignments
    :param assignment_names_to_get: Specific assignment names to retrieve.
    :return: List of Assignment() objects
    """
    all_assignment_jsons = mod_assign_get_assignments(course_id)
    assignment_ids = [assign['id'] for assign in all_assignment_jsons]

    grades = mod_assign_get_grades(assignment_ids)
    submissions = mod_assign_get_submissions(assignment_ids)
    assignments = []

    assignments_not_found = None
    if assignment_names_to_get:
        assignments_not_found = assignment_names_to_get[:]

    for assignment in all_assignment_jsons:
        # Filter specific assignment names
        if assignment_names_to_get and assignment['name'] not in \
                assignment_names_to_get:
            continue

        assignments.append(Assignment(assignment,
                                      submissions.get(assignment['id'], []),
                                      grades.get(assignment['id'], [])))

        if assignments_not_found is not None:
            assignments_not_found.remove(assignment['name'])

    if assignments_not_found:
        logger.error("Could not find the following exercises for the trainer: "
                     "%s", assignments_not_found)

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

    for attachment in assignment[0].attachments:
        assignment_files.append(attachment)

    return assignment_files
