import requests

from moodler.consts import REQUEST_FORMAT


class MissingGrade(Exception):
    pass


class Grade(object):
    def __init__(self, grade_json):
        self.timestamp = grade_json['timemodified']
        try:
            self.grade = float(grade_json['grade'])
        except ValueError:
            raise MissingGrade()
        self._json_data = grade_json

    def __repr__(self):
        return 'Grade(grade={}, timestamp={})'.format(self.grade, self.timestamp)


class SubmissionFile(object):
    def __init__(self, submission_file_json):
        self.url = submission_file_json['fileurl']
        self.timestamp = submission_file_json['timemodified']
        self._json_data = submission_file_json

    def __repr__(self):
        return 'SubmissionFile(url={}, timestamp={})'.format(self.url, self.timestamp)


class Submission(object):
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

        # Useful for debugging
        self._submission_json = submission_json

    @property
    def submitted(self):
        return 'submitted' == self.status

    def needs_grading(self):
        """
        Returns True if the submission needs grading.
        Does this by checking the grading status and also checks for resubmissions by comparing the timestamps of the grade to the submission files
        """
        if self.submitted:
            if 'notgraded' == self.gradingstatus:
                return True
            if self.grade is not None \
               and 0 < len(self.submission_files) \
               and self.grade.timestamp - max([sf.timestamp for sf in self.submission_files]) < 0:
                return True

        return False

    def __repr__(self):
        return 'Submission(user_id={}, status={}, gradingstatus={}, grade={}, submitted={})'.format(self.user_id,
                                                                                                    self.status,
                                                                                                    self.gradingstatus,
                                                                                                    self.grade,
                                                                                                    len(self.submission_files))


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

    submissions = {}
    for assign in response.json()['assignments']:
        submissions[assign['assignmentid']] = assign['submissions']
    return submissions


def mod_assign_get_submission_status(assignment_id, user_id=None):
    """
    Returns the submissions for the given assignments in a dict
    mapping assignment id to submissions
    {id: [..]}
    """
    url = REQUEST_FORMAT.format('mod_assign_get_submission_status')
    url += '&assignid={}'.format(assignment_id)

    if user_id is not None:
        url += '&userid={}'.format(user_id)

    response = requests.get(url)
    return response.json()
