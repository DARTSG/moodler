from enum import Enum

from moodler.moodle_api import call_moodle_api
from moodler.moodle_exception import MoodlerException


class SubmissionStatus(Enum):
    NEW = "new"
    SUBMITTED = "submitted"


class MissingGrade(MoodlerException):
    pass


class Grade(object):
    def __init__(self, grade_json):
        self.timestamp = grade_json["timemodified"]
        try:
            self.grade = float(grade_json["grade"])
        except ValueError:
            raise MissingGrade()
        self._json_data = grade_json

    def __repr__(self):
        return "Grade(grade={}, timestamp={})".format(self.grade, self.timestamp)


class SubmissionFile(object):
    def __init__(self, submission_file_json):
        self.url = submission_file_json["fileurl"]
        self.timestamp = submission_file_json["timemodified"]
        self._json_data = submission_file_json

    def __repr__(self):
        return "SubmissionFile(url={}, timestamp={})".format(self.url, self.timestamp)


class Submission(object):
    def __init__(self, user_id, grade_json, submission_json):
        self.user_id = user_id

        if grade_json is not None:
            self.grade = Grade(grade_json)
        else:
            self.grade = None

        self.status = submission_json["status"]
        self.gradingstatus = submission_json["gradingstatus"]
        self.submission_files = []
        self.timestamp = submission_json["timemodified"]

        for plugin in submission_json["plugins"]:
            if "file" != plugin["type"]:
                continue
            for filearea in plugin["fileareas"]:
                for f in filearea["files"]:
                    self.submission_files.append(SubmissionFile(f))

        # Useful for debugging
        self._submission_json = submission_json

    @property
    def resubmitted(self):
        # Returns true if the submission was edited after the last grading
        return self.grade is not None and self.grade.timestamp <= self.timestamp

    def needs_grading(self):
        """
        Returns True if the submission needs grading.
        Does this by checking the grading status and the grading timestamp vs the last modification timestamp
        # See https://github.com/moodle/moodle/blob/master/mod/assign/locallib.php#L2467
        """
        return all(
            [
                self.timestamp is not None,
                self.status == SubmissionStatus.SUBMITTED.value,
                any(
                    [
                        self.grade is None,
                        self.resubmitted,
                        self.grade is not None
                        and (
                            self.grade.timestamp is None
                            or (self.grade.grade is not None and self.grade.grade < 0)
                        ),
                    ]
                ),
            ]
        )

    def __repr__(self):
        return (
            "Submission(user_id={}, gradingstatus={}, grade={}, "
            "submitted={})".format(
                self.user_id,
                self.gradingstatus,
                self.grade,
                len(self.submission_files),
            )
        )


def mod_assign_get_submissions(assignment_ids):
    """
    Returns the submissions for the given assignments in a dict
    mapping assignment id to submissions
    {id: [..]}
    """
    response = call_moodle_api(
        "mod_assign_get_submissions", assignmentids=assignment_ids
    )

    submissions = {}
    for assign in response["assignments"]:
        submissions[assign["assignmentid"]] = assign["submissions"]

    return submissions


def mod_assign_get_submission_status(assignment_id, user_id=None):
    """
    Returns the submissions for the given assignments in a dict
    mapping assignment id to submissions
    {id: [..]}
    """
    response = call_moodle_api(
        "mod_assign_get_submission_status",
        assignid=assignment_id,
        userid=user_id,
    )

    return response
