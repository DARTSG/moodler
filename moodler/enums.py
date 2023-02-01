from enum import Enum, IntEnum, auto


class WorkflowState(Enum):
    """
    The next marking workflow state
    One advantage of using marking workflow is that the grades can be hidden from students until
    they are set to 'Released'.
    See https://docs.moodle.org/401/en/Assignment_settings#Grade
    """

    NOT_MARKED = "notmarked"  # the marker has not yet started
    IN_MARKING = "inmarking"  # the marker has started but not yet finished
    MARKING_COMPLETED = "markingcompleted"  # the marker has finished but might need to go back for checking/corrections
    IN_REVIEW = (
        "inreview"  # the marking is now with the teacher in charge for quality checking
    )
    READY_FOR_RELEASE = "readyforrelease"  # the teacher in charge is satisfied with the marking but wait before giving students access to the marking
    RELEASED = "released"  # the student can access the grades/feedback


class CommentFormat(IntEnum):
    MOODLE = 0
    HTML = 1
    PLAIN = 2
    MARKDOWN = 4


# See https://github.com/moodle/moodle/blob/df502b3/mod/assign/locallib.php#L30-L33
class SubmissionStatus(Enum):
    NEW = auto()
    # If instructor has enabled draft mode, your assignment Submission status will be Draft
    # (not submitted) until the `Submit` assignment button is selected.
    # the process.
    DRAFT = auto()
    # When your assignment has been fully submitted, you will see the Submission status indicated
    # as Submitted for grading.
    SUBMITTED = auto()
    # If the submission setting 'Attempts reopened' is set to 'Automatically until pass' and
    # a submission is graded below the grade to pass, then then submission is automatically
    # unlocked when the grade is saved. Similarly, if the submission setting 'Attempts reopened'
    # is set to Manually, and a teacher selects 'Allow another attempt, then the submission is
    # automatically unlocked.
    REOPENED = auto()
