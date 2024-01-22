import os

from moodler.assignment import Assignment
from moodler.submission import Submission, SubmissionStatus

os.environ["LTI_TOKEN"] = ""
os.environ["LTI_URL"] = ""

ASSIGNMENT_JSON = {
    "id": 1,
    "cmid": 1,
    "course": 1,
    "name": "Assignment Name",
    "nosubmissions": 0,
    "submissiondrafts": 0,
    "sendnotifications": 0,
    "sendlatenotifications": 0,
    "sendstudentnotifications": 1,
    "duedate": 0,
    "allowsubmissionsfromdate": 0,
    "grade": 100,
    "timemodified": 1676039979,
    "completionsubmit": 1,
    "cutoffdate": 0,
    "gradingduedate": 0,
    "teamsubmission": 0,
    "requireallteammemberssubmit": 0,
    "teamsubmissiongroupingid": 0,
    "blindmarking": 0,
    "hidegrader": 0,
    "revealidentities": 0,
    "attemptreopenmethod": "none",
    "maxattempts": -1,
    "markingworkflow": 1,
    "markingallocation": 1,
    "requiresubmissionstatement": 0,
    "preventsubmissionnotingroup": 0,
    "configs": [
        {
            "plugin": "onlinetext",
            "subtype": "assignsubmission",
            "name": "enabled",
            "value": "1",
        },
        {
            "plugin": "onlinetext",
            "subtype": "assignsubmission",
            "name": "wordlimit",
            "value": "0",
        },
        {
            "plugin": "onlinetext",
            "subtype": "assignsubmission",
            "name": "wordlimitenabled",
            "value": "0",
        },
        {
            "plugin": "file",
            "subtype": "assignsubmission",
            "name": "enabled",
            "value": "1",
        },
        {
            "plugin": "file",
            "subtype": "assignsubmission",
            "name": "maxfilesubmissions",
            "value": "20",
        },
        {
            "plugin": "file",
            "subtype": "assignsubmission",
            "name": "maxsubmissionsizebytes",
            "value": "53687091200",
        },
        {
            "plugin": "file",
            "subtype": "assignsubmission",
            "name": "filetypeslist",
            "value": "",
        },
        {
            "plugin": "comments",
            "subtype": "assignsubmission",
            "name": "enabled",
            "value": "1",
        },
        {
            "plugin": "comments",
            "subtype": "assignfeedback",
            "name": "enabled",
            "value": "1",
        },
        {
            "plugin": "comments",
            "subtype": "assignfeedback",
            "name": "commentinline",
            "value": "0",
        },
        {
            "plugin": "offline",
            "subtype": "assignfeedback",
            "name": "enabled",
            "value": "1",
        },
    ],
    "intro": "",
    "introformat": 1,
    "introfiles": [],
    "introattachments": [
        {
            "filename": "filename.pdf",
            "filepath": "/",
            "filesize": 60796,
            "fileurl": "http://example.com/webservice/pluginfile.php/0000/mod_assign/introattachment/0/filename.pdf",
            "timemodified": 1674715676,
            "mimetype": "application/pdf",
            "isexternalfile": False,
        }
    ],
    "timelimit": 0,
    "submissionattachments": 0,
}

SUBMISSIONS_JSON = [
    {
        "id": 1,
        "userid": 1,
        "attemptnumber": 0,
        "timecreated": 1674749069,
        "timemodified": 1674749072,
        "timestarted": None,
        "status": SubmissionStatus.DRAFT.value,
        "groupid": 0,
        "plugins": [
            {
                "type": "onlinetext",
                "name": "Online text",
                "fileareas": [{"area": "submissions_onlinetext", "files": []}],
                "editorfields": [
                    {
                        "name": "onlinetext",
                        "description": "Online text submissions",
                        "text": "a",
                        "format": 1,
                    }
                ],
            },
            {
                "type": "file",
                "name": "File submissions",
                "fileareas": [{"area": "submission_files", "files": []}],
            },
            {"type": "comments", "name": "Submission comments"},
        ],
        "gradingstatus": "not graded",
    },
    {
        "id": 32,
        "userid": 32,
        "attemptnumber": 0,
        "timecreated": 1675095675,
        "timemodified": 1676019314,
        "timestarted": None,
        "status": SubmissionStatus.SUBMITTED.value,
        "groupid": 0,
        "plugins": [
            {
                "type": "onlinetext",
                "name": "Online text",
                "fileareas": [{"area": "submissions_onlinetext", "files": []}],
                "editorfields": [
                    {
                        "name": "onlinetext",
                        "description": "Online text submissions",
                        "text": "",
                        "format": 1,
                    }
                ],
            },
            {
                "type": "file",
                "name": "File submissions",
                "fileareas": [
                    {
                        "area": "submission_files",
                        "files": [
                            {
                                "filename": "filename.py",
                                "filepath": "/",
                                "filesize": 418,
                                "fileurl": "http://example.com/webservice/pluginfile.php/0000/assignsubmission_file/submission_files/32/filename.py",
                                "timemodified": 1676019314,
                                "mimetype": "document/unknown",
                                "isexternalfile": False,
                            }
                        ],
                    }
                ],
            },
            {"type": "comments", "name": "Submission comments"},
        ],
        "gradingstatus": "released",
    },
    {
        "id": 33,
        "userid": 33,
        "attemptnumber": 0,
        "timecreated": 1675095710,
        "timemodified": 1675095716,
        "timestarted": None,
        "status": SubmissionStatus.SUBMITTED.value,
        "groupid": 0,
        "plugins": [
            {
                "type": "onlinetext",
                "name": "Online text",
                "fileareas": [{"area": "submissions_onlinetext", "files": []}],
                "editorfields": [
                    {
                        "name": "onlinetext",
                        "description": "Online text submissions",
                        "text": "",
                        "format": 1,
                    }
                ],
            },
            {
                "type": "file",
                "name": "File submissions",
                "fileareas": [
                    {
                        "area": "submission_files",
                        "files": [
                            {
                                "filename": "03.filename.py",
                                "filepath": "/",
                                "filesize": 324,
                                "fileurl": "http://example.com/webservice/pluginfile.php/0000/assignsubmission_file/submission_files/33/03.filename.py",
                                "timemodified": 1675095716,
                                "mimetype": "text/plain",
                                "isexternalfile": False,
                            }
                        ],
                    }
                ],
            },
            {"type": "comments", "name": "Submission comments"},
        ],
        "gradingstatus": "released",
    },
]

GRADES_JSON = [
    {
        "id": 1,
        "userid": 1,
        "attemptnumber": 0,
        "timecreated": 1674749705,
        "timemodified": 1675431369,
        "grader": 911,
        "grade": "0.00000",
    },
    {
        "id": 32,
        "userid": 32,
        "attemptnumber": 0,
        "timecreated": 1675097169,
        "timemodified": 1675174901,
        "grader": 911,
        "grade": "65.00000",
    },
    {
        "id": 33,
        "userid": 33,
        "attemptnumber": 0,
        "timecreated": 1675096209,
        "timemodified": 1675178765,
        "grader": 911,
        "grade": "100.00000",
    },
]


def test_assignment():
    assignment = Assignment(ASSIGNMENT_JSON, SUBMISSIONS_JSON, GRADES_JSON)
    assert assignment.name == "Assignment Name"
    assert assignment.uid == ASSIGNMENT_JSON["id"]
    assert assignment.cmid == ASSIGNMENT_JSON["cmid"]
    assert assignment.description == ASSIGNMENT_JSON["intro"]

    assert len(assignment.submissions) == 3
    assert len(assignment.ungraded()) == 1
    assert len(assignment.submitted()) == 2


def test_submission_submitted():
    user_id = GRADES_JSON[2]["userid"]
    submission = Submission(user_id, GRADES_JSON[2], SUBMISSIONS_JSON[2])
    assert submission.grade.grade == 100.0
    assert submission.user_id == user_id
    assert submission.status == SubmissionStatus.SUBMITTED.value
    assert submission.attemptnumber == 0
    assert submission.gradingstatus == "released"
    assert len(submission.submission_files) == 1
    assert submission.released
    assert not submission.resubmitted
    assert not submission.needs_grading()


def test_submission_notsubmitted():
    user_id = GRADES_JSON[0]["userid"]
    submission = Submission(user_id, GRADES_JSON[0], SUBMISSIONS_JSON[0])
    assert submission.grade.grade == 0.0
    assert submission.user_id == user_id
    assert submission.status == SubmissionStatus.DRAFT.value
    assert submission.attemptnumber == 0
    assert submission.gradingstatus == "not graded"
    assert len(submission.submission_files) == 0
    assert not submission.released
    assert not submission.resubmitted
    # Not submitted submissions does not require grading
    assert not submission.needs_grading()


def test_submission_ungraded():
    user_id = GRADES_JSON[1]["userid"]
    submission = Submission(user_id, GRADES_JSON[1], SUBMISSIONS_JSON[1])
    assert submission.grade.grade == 65.0
    assert submission.user_id == user_id
    assert submission.status == SubmissionStatus.SUBMITTED.value
    assert submission.attemptnumber == 0
    assert submission.gradingstatus == "released"
    assert len(submission.submission_files) == 1
    assert submission.released
    assert submission.resubmitted
    assert submission.needs_grading()
