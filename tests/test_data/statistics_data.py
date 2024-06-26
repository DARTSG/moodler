from moodler.moodle import SubmissionStatistics, ExerciseStatistics


class NoGroups:
    NO_SUBMISSIONS = {
        "null": SubmissionStatistics(
            total_submissions=0,
            total_ungraded=0,
            total_resubmissions=0,
            total_unreleased=0,
            exercises={
                "Assignment 1": ExerciseStatistics(
                    submissions=0,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=0
                ),
                "Assignment 2": ExerciseStatistics(
                    submissions=0,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=0
                ),
            }
        )
    }

    UNGRADED_SUBMISSIONS = {
        "null": SubmissionStatistics(
            total_submissions=4,
            total_ungraded=4,
            total_resubmissions=0,
            total_unreleased=0,
            exercises={
                "Assignment 1": ExerciseStatistics(
                    submissions=2,
                    ungraded=2,
                    resubmissions=0,
                    unreleased=0
                ),
                "Assignment 2": ExerciseStatistics(
                    submissions=2,
                    ungraded=2,
                    resubmissions=0,
                    unreleased=0
                ),
            }
        )
    }

    GRADED_SUBMISSIONS = {
        "null": SubmissionStatistics(
            total_submissions=4,
            total_ungraded=0,
            total_resubmissions=0,
            total_unreleased=0,
            exercises={
                "Assignment 1": ExerciseStatistics(
                    submissions=2,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=0
                ),
                "Assignment 2": ExerciseStatistics(
                    submissions=2,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=0
                ),
            }
        )
    }

    RESUBMISSIONS = {
        "null": SubmissionStatistics(
            total_submissions=8,
            total_ungraded=4,
            total_resubmissions=4,
            total_unreleased=0,
            exercises={
                "Assignment 1": ExerciseStatistics(
                    submissions=4,
                    ungraded=2,
                    resubmissions=2,
                    unreleased=0
                ),
                "Assignment 2": ExerciseStatistics(
                    submissions=4,
                    ungraded=2,
                    resubmissions=2,
                    unreleased=0
                ),
            }
        )
    }

    UNRELEASED_GRADES = {
        "null": SubmissionStatistics(
            total_submissions=4,
            total_ungraded=0,
            total_resubmissions=0,
            total_unreleased=4,
            exercises={
                "Assignment 1": ExerciseStatistics(
                    submissions=2,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=2
                ),
                "Assignment 2": ExerciseStatistics(
                    submissions=2,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=2
                ),
            }
        )
    }


class WithGroups:
    NO_SUBMISSIONS = {
        "Group 1": SubmissionStatistics(
            total_submissions=0,
            total_ungraded=0,
            total_resubmissions=0,
            total_unreleased=0,
            exercises={
                "Assignment 1": ExerciseStatistics(
                    submissions=0,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=0
                ),
                "Assignment 2": ExerciseStatistics(
                    submissions=0,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=0
                ),
            }
        ),
        "Group 2": SubmissionStatistics(
            total_submissions=0,
            total_ungraded=0,
            total_resubmissions=0,
            total_unreleased=0,
            exercises={
                "Assignment 1": ExerciseStatistics(
                    submissions=0,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=0
                ),
                "Assignment 2": ExerciseStatistics(
                    submissions=0,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=0
                ),
            }
        )
    }

    UNGRADED_SUBMISSIONS = {
        "Group 1": SubmissionStatistics(
            total_submissions=2,
            total_ungraded=2,
            total_resubmissions=0,
            total_unreleased=0,
            exercises={
                "Assignment 1": ExerciseStatistics(
                    submissions=1,
                    ungraded=1,
                    resubmissions=0,
                    unreleased=0
                ),
                "Assignment 2": ExerciseStatistics(
                    submissions=1,
                    ungraded=1,
                    resubmissions=0,
                    unreleased=0
                ),
            }
        ),
        "Group 2": SubmissionStatistics(
            total_submissions=2,
            total_ungraded=2,
            total_resubmissions=0,
            total_unreleased=0,
            exercises={
                "Assignment 1": ExerciseStatistics(
                    submissions=1,
                    ungraded=1,
                    resubmissions=0,
                    unreleased=0
                ),
                "Assignment 2": ExerciseStatistics(
                    submissions=1,
                    ungraded=1,
                    resubmissions=0,
                    unreleased=0
                ),
            }
        )
    }

    GRADED_SUBMISSIONS = {
        "Group 1": SubmissionStatistics(
            total_submissions=2,
            total_ungraded=0,
            total_resubmissions=0,
            total_unreleased=0,
            exercises={
                "Assignment 1": ExerciseStatistics(
                    submissions=1,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=0
                ),
                "Assignment 2": ExerciseStatistics(
                    submissions=1,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=0
                ),
            }
        ),
        "Group 2": SubmissionStatistics(
            total_submissions=2,
            total_ungraded=0,
            total_resubmissions=0,
            total_unreleased=0,
            exercises={
                "Assignment 1": ExerciseStatistics(
                    submissions=1,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=0
                ),
                "Assignment 2": ExerciseStatistics(
                    submissions=1,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=0
                ),
            }
        )
    }

    RESUBMISSIONS = {
        "Group 1": SubmissionStatistics(
            total_submissions=4,
            total_ungraded=2,
            total_resubmissions=2,
            total_unreleased=0,
            exercises={
                "Assignment 1": ExerciseStatistics(
                    submissions=2,
                    ungraded=1,
                    resubmissions=1,
                    unreleased=0
                ),
                "Assignment 2": ExerciseStatistics(
                    submissions=2,
                    ungraded=1,
                    resubmissions=1,
                    unreleased=0
                ),
            }
        ),
        "Group 2": SubmissionStatistics(
            total_submissions=4,
            total_ungraded=2,
            total_resubmissions=2,
            total_unreleased=0,
            exercises={
                "Assignment 1": ExerciseStatistics(
                    submissions=2,
                    ungraded=1,
                    resubmissions=1,
                    unreleased=0
                ),
                "Assignment 2": ExerciseStatistics(
                    submissions=2,
                    ungraded=1,
                    resubmissions=1,
                    unreleased=0
                ),
            }
        )
    }

    UNRELEASED_GRADES = {
        "Group 1": SubmissionStatistics(
            total_submissions=2,
            total_ungraded=0,
            total_resubmissions=0,
            total_unreleased=2,
            exercises={
                "Assignment 1": ExerciseStatistics(
                    submissions=1,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=1
                ),
                "Assignment 2": ExerciseStatistics(
                    submissions=1,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=1
                ),
            }
        ),
        "Group 2": SubmissionStatistics(
            total_submissions=2,
            total_ungraded=0,
            total_resubmissions=0,
            total_unreleased=2,
            exercises={
                "Assignment 1": ExerciseStatistics(
                    submissions=1,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=1
                ),
                "Assignment 2": ExerciseStatistics(
                    submissions=1,
                    ungraded=0,
                    resubmissions=0,
                    unreleased=1
                ),
            }
        ),
    }
