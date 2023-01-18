import pytest

from moodler.urlencode import urlencode


@pytest.mark.parametrize(
    "input,expected",
    (
        (
            {
                "assignmentid": 1,
                "applytoall": 1,
            },
            "assignmentid=1&applytoall=1",
        ),
        (
            {
                "assignmentid": 1,
                "applytoall": 1,
                "grades": [
                    {
                        "userid": 1,
                        "grade": 0.0,
                        "attemptnumber": -1,
                        "addattempt": 0,
                        "workflowstate": "inreview",
                        "plugindata": {
                            "assignfeedbackcomments_editor": {
                                "format": 4,
                                "text": "**Feedbacks: 1**",
                            }
                        },
                    },
                    {
                        "userid": 2,
                        "grade": 50.0,
                        "attemptnumber": -1,
                        "addattempt": 0,
                        "workflowstate": "released",
                        "plugindata": {
                            "assignfeedbackcomments_editor": {
                                "format": 4,
                                "text": "**Feedbacks: 2**",
                            }
                        },
                    },
                ],
            },
            (
                "assignmentid=1&"
                "applytoall=1&"
                "grades[0][userid]=1&"
                "grades[0][grade]=0.0&"
                "grades[0][attemptnumber]=-1&"
                "grades[0][addattempt]=0&"
                "grades[0][workflowstate]=inreview&"
                "grades[0][plugindata][assignfeedbackcomments_editor][format]=4&"
                "grades[0][plugindata][assignfeedbackcomments_editor][text]=%2A%2AFeedbacks%3A+1%2A%2A&"
                "grades[1][userid]=2&"
                "grades[1][grade]=50.0&"
                "grades[1][attemptnumber]=-1&"
                "grades[1][addattempt]=0&"
                "grades[1][workflowstate]=released&"
                "grades[1][plugindata][assignfeedbackcomments_editor][format]=4&"
                "grades[1][plugindata][assignfeedbackcomments_editor][text]=%2A%2AFeedbacks%3A+2%2A%2A"
            ),
        ),
    ),
)
def test_urlencode(input, expected):
    assert urlencode(input) == expected
