import pytest

from moodler.moodle import submissions_statistics
from moodler.assignment import Assignment
from moodler.groups import Group

from .test_data.statistics_data import NoGroups, WithGroups


class TestSubmissionStatistics:
    """
    Check that the statistics of the submissions are retrieved correctly

    Cases:
    - 2 Assignments, 0 Submissions, 0 Grades
    - 2 Assignments, 2 Submissions, 0 Grades
    - 2 Assignments, 2 Submissions, 2 Grades
    - 2 Assignments, 2 Submissions, 2 Grades, 2 Resubmissions
    - 2 Assignments, 2 Submissions, 2 Grades, 2 Unreleased
    """
    students = {1: "Student One", 2: "Student Two"}
    groups = [Group({"id": 1, "name": "Group 1"}), Group({"id": 2, "name": "Group 2"})]
    group_map = {1: "Group 1", 2: "Group 2"}
    group_users = [{'groupid': 1, 'userids': [1]}, {'groupid': 2, 'userids': [2]}]
    assignment_json = [
        {"id": 1, "cmid": 1, "name": "Assignment 1"},
        {"id": 2, "cmid": 2, "name": "Assignment 2"},
    ]

    @pytest.mark.parametrize("groups, expected_result", [
        ([], NoGroups.NO_SUBMISSIONS),
        (groups, WithGroups.NO_SUBMISSIONS),
    ])
    def test_no_submissions(self, mocker, groups, expected_result):
        """
        Course that has no submissions
        """
        assignments = [
            Assignment(assignment,[],[])
            for assignment in self.assignment_json
        ]

        mocker.patch("moodler.assignment.get_assignments_by_field", return_value=assignments)
        mocker.patch("moodler.groups.get_course_groups", return_value=groups)
        mocker.patch("moodler.groups.get_group_users", return_value=self.group_users)
        mocker.patch("moodler.students.core_enrol_get_enrolled_users", return_value={})

        assert submissions_statistics(1, groups) == expected_result

    @pytest.mark.parametrize("groups, expected_result", [
        ([], NoGroups.UNGRADED_SUBMISSIONS),
        (groups, WithGroups.UNGRADED_SUBMISSIONS),
    ])
    def test_ungraded_submissions(self, mocker, groups, expected_result):
        """
        Course that has submissions which are ungraded
        """
        submission_json = [
            {"userid": 1, "status": "submitted", "attemptnumber": 0, "gradingstatus": "notgraded", "timemodified": 1718254280, "plugins": []},
            {"userid": 2, "status": "submitted", "attemptnumber": 0, "gradingstatus": "notgraded", "timemodified": 1718254280, "plugins": []},
        ]

        assignments = [
            Assignment(assignment,submission_json,[])
            for assignment in self.assignment_json
        ]

        mocker.patch("moodler.assignment.get_assignments_by_field", return_value=assignments)
        mocker.patch("moodler.groups.get_course_groups", return_value=groups)
        mocker.patch("moodler.groups.get_group_users", return_value=self.group_users)
        mocker.patch("moodler.students.core_enrol_get_enrolled_users", return_value={})

        assert submissions_statistics(1, groups) == expected_result

    @pytest.mark.skip(reason="Not implemented yet")
    @pytest.mark.parametrize("groups, expected_result", [
        ([], NoGroups.GRADED_SUBMISSIONS),
        (groups, WithGroups.GRADED_SUBMISSIONS),
    ])
    def test_graded_submissions(self, mocker, groups, expected_result):
        """
        Course that has submissions that are graded
        """
        assert submissions_statistics(1, groups) == expected_result

    @pytest.mark.skip(reason="Not implemented yet")
    @pytest.mark.parametrize("groups, expected_result", [
        ([], NoGroups.RESUBMISSIONS),
        (groups, WithGroups.RESUBMISSIONS),
    ])
    def test_resubmissions(self, mocker, groups, expected_result):
        """
        Course that contains submissions after previous submissions have been graded
        """
        assert submissions_statistics(1, groups) == expected_result

    @pytest.mark.skip(reason="Not implemented yet")
    @pytest.mark.parametrize("groups, expected_result", [
        ([], NoGroups.UNRELEASED_GRADES),
        (groups, WithGroups.UNRELEASED_GRADES),
    ])
    def test_unreleased_grades(self, mocker, groups, expected_result):
        """
        Course that contain grades that are not released to the student yet
        """
        assert submissions_statistics(1, groups) == expected_result
