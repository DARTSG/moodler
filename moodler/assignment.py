import logging

from moodler.config import URL
from moodler.moodle_api import call_moodle_api
from moodler.moodle_exception import MoodlerException
from moodler.students import get_students, get_students_ids_by_name, get_user_name
from moodler.submission import MissingGrade, Submission, mod_assign_get_submissions

logger = logging.getLogger(__name__)


class AssignmentException(MoodlerException):
    pass


class InvalidAssignmentID(AssignmentException):
    pass


class EmptyCourseError(AssignmentException):
    pass


class Assignment(object):
    def __init__(self, assignment_json, submissions_json, grades_json):
        # a random number Moodle generates in API (not seen when you use Moodle visually)
        self.uid = assignment_json["id"]
        # the actual ID that you see in the Moodle interface
        self.cmid = assignment_json["cmid"]
        self.name = assignment_json["name"]
        self.description = assignment_json.get("intro", "")
        self.attachments: list[str] = [
            attachment["fileurl"]
            for attachment in assignment_json.get("introattachments", [])
        ]

        self.submissions: list[Submission] = []
        for submission in submissions_json:
            grade_json = None
            user_id = submission["userid"]
            for grade in grades_json:
                if user_id == grade["userid"]:
                    grade_json = grade
                    break
            if "new" != submission["status"]:
                try:
                    self.submissions.append(Submission(user_id, grade_json, submission))
                except MissingGrade:
                    logger.warning(
                        'Missing grade for student "{}" in assignment "{}". Fix ASAP at {}'.format(
                            get_user_name(user_id),
                            self.name,
                            "{}//mod/assign/view.php?id={}&action=grader&userid={}".format(
                                URL, self.cmid, user_id
                            ),
                        )
                    )
                    self.submissions.append(Submission(user_id, None, submission))

        self._assignment_json = assignment_json
        self._submissions_json = submissions_json
        self._grades_json = grades_json

    def ungraded(self):
        submissions: list[Submission] = []
        for submission in self.submissions:
            # Process ungraded submission
            if submission.needs_grading():
                submissions.append(submission)
        return submissions

    def __repr__(self):
        return "Assignment(id={}, name={}, submissions={})".format(
            self.uid, self.name, len(self.submissions)
        )

    def lock_submissions(
        self, course_id, students_names=None, only_lock_resubmissions=True
    ):
        """
        Locking submissions for this specific assignment.
        """
        if students_names is None:
            students_ids = list(get_students(course_id).keys())
        else:
            students_ids = get_students_ids_by_name(course_id, students_names)

        if only_lock_resubmissions:
            submitted_users = [sub.user_id for sub in self.submissions]
            students_ids = set(submitted_users).intersection(students_ids)

        if not students_ids:
            logger.warning("No student was found! Aborting...")
        else:
            mod_assign_lock_submissions(self.uid, list(students_ids))

            logger.info(
                "Locked submissions for assignment '%s' for %s",
                self.name,
                students_names
                if students_names is not None
                else "all students"
                + (" that submitted the exercise" if only_lock_resubmissions else ""),
            )

    def unlock_submissions(self, course_id, students_names=None):
        """
        Locking submissions for this specific assignment.
        """
        if students_names is None:
            students_ids = list(get_students(course_id).keys())
        else:
            students_ids = get_students_ids_by_name(course_id, students_names)

        if not students_ids:
            logger.warning("No student was found! Aborting...")
        else:
            mod_assign_unlock_submissions(self.uid, students_ids)

            logger.info(
                "Unlocked submissions for assignment '%s' for %s",
                self.name,
                students_names if students_names is not None else "all students.",
            )


def mod_assign_lock_submissions(assignment_id, user_ids):
    """
    Locks submissions for a specific assignments for a specific user(s).
    """
    call_moodle_api(
        "mod_assign_lock_submissions",
        assignmentid=assignment_id,
        userids=user_ids,
    )


def mod_assign_unlock_submissions(assignment_id, user_ids):
    """
    Unlocks submissions for a specific assignments for a specific user(s).
    """
    call_moodle_api(
        "mod_assign_unlock_submissions",
        assignmentid=assignment_id,
        userids=user_ids,
    )


def mod_assign_get_grades(assignment_ids):
    """
    Returns the grades for all the assignments
    """
    response = call_moodle_api("mod_assign_get_grades", assignmentids=assignment_ids)

    grades = {}
    for grds in response["assignments"]:
        grades[grds["assignmentid"]] = grds["grades"]

    return grades


def mod_assign_get_assignments(course_id):
    """
    Returns a dictionary mapping assignment id to its name from a specified
    course
    """
    response = call_moodle_api("mod_assign_get_assignments", courseids=[course_id])

    if not response["courses"]:
        raise EmptyCourseError(
            """Received an empty course.
            It could be that the course does not have any assignments.\n{}""".format(
                response
            )
        )

    return response["courses"][0]["assignments"]


def get_assignments_by_field(
    course_id, field=None, assignments_fields=None
) -> list[Assignment] | None:
    """
    Retrieves assignments, grades, and submissions from server and parses into
    corresponding objects. This is a generic function to retrieve assignments
    base on a specific field that is also received in the paramaters.

    :param course_id: The ID of the course to retrieve its assignments
    :param field: The field in the assignment by which to tell which
    assignments to retrieve.
    :param assignments_fields: The fields in the assignments by which to
    retrieve the assignments. If the field `field` in the assignment is in
    this list, then the assignment will be retrieved.
    :return: List of Assignment() objects
    """
    assignments_not_found = []
    all_assignment_jsons = mod_assign_get_assignments(course_id)
    assignment_ids = [assign["id"] for assign in all_assignment_jsons]

    if not assignment_ids:
        logger.warning("No assignments were detected for course %s", course_id)
        return None

    grades = mod_assign_get_grades(assignment_ids)
    submissions = mod_assign_get_submissions(assignment_ids)
    assignments: list[Assignment] = []

    if assignments_fields:
        assignments_not_found = assignments_fields[:]

    for assignment in all_assignment_jsons:
        # Filter specific assignment IDs
        if assignments_fields and field:
            if assignment[field] not in assignments_fields:
                continue

            assignments_not_found.remove(assignment[field])

        assignments.append(
            Assignment(
                assignment,
                submissions.get(assignment["id"], []),
                grades.get(assignment["id"], []),
            )
        )

    if assignments_not_found:
        logger.error(
            "Could not find the following exercises for the trainer: " "%s",
            assignments_not_found,
        )

    return assignments


def get_assignments(course_id, assignment_ids_to_get=None) -> list[Assignment] | None:
    """
    Retrieves assignments, grades, and submissions from server and parses into corresponding objects.

    :param course_id: The ID of the course to retrieve its assignments
    :param assignment_ids_to_get: Specific assignment IDs to retrieve.
    :return: List of Assignment() objects
    """
    return get_assignments_by_field(
        course_id, assignments_fields=assignment_ids_to_get, field="cmid"
    )


def get_assignments_by_names(course_id, assignment_names_to_get=None):
    """
    Retrieves assignments, grades, and submissions from server and parses into corresponding objects.

    :param course_id: The ID of the course to retrieve its assignments
    :param assignment_names_to_get: Specific assignment names to retrieve.
    :return: List of Assignment() objects
    """
    assignments = get_assignments_by_field(
        course_id, assignments_fields=assignment_names_to_get, field="name"
    )

    return assignments


def get_assignment_files(course_id, assignment_id) -> list[str]:
    """
    Returns a list of all the file URLs for the assignment received.
    :param course_id: The ID of the course to which the assignment belongs.
    :param assignment_id: The ID of the assignment to retrieve its files.
    :return: List of all the files related to this assignment.
    """
    assignment_files: list[str] = []

    # Retrieve only the files for this specific assignment ID
    assignment = get_assignments(course_id, [assignment_id])
    if assignment is None:
        raise InvalidAssignmentID()

    for attachment in assignment[0].attachments:
        assignment_files.append(attachment)

    return assignment_files
