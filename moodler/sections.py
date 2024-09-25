import logging
from collections import defaultdict
from typing import Dict, Iterable, List, NamedTuple, Optional

from parse import parse

from moodler.assignment import get_assignments
from moodler.moodle_api import call_moodle_api

logger = logging.getLogger(__name__)


class Course(NamedTuple):
    id: str
    prefix: str
    name: str

    @property
    def full_name(self):
        return f"{self.prefix} {self.name}"


def core_course_get_courses():
    """
    Returns a tuple of ids and course names
    """
    return call_moodle_api("core_course_get_courses")


def core_course_get_contents(course_id):
    """
    Returns the structure of the course with all resources and topics
    """
    return call_moodle_api("core_course_get_contents", courseid=course_id)


def list_courses(course_prefix: str = "") -> Iterable[Course]:
    """
    List courses in moodle, optionally filter by course_prefix
    """
    courses_from_moodle = core_course_get_courses()

    for course in courses_from_moodle:
        full_name = course["fullname"]
        if not course["shortname"].startswith(
            course_prefix
        ) and not full_name.startswith(course_prefix):
            continue

        course_name = full_name
        if course_prefix:
            course_name_format = f"{course_prefix} - {{course_name}}"
            course_name_match = parse(course_name_format, full_name)

            if course_name_match is None:
                continue

            course_name = course_name_match["course_name"]

        yield Course(course["id"], prefix=course_prefix, name=course_name)


def get_course_by_id(course_id: str) -> Optional[Course]:
    for course in list_courses():
        if course.id == course_id:
            return course

    return None


def get_assignments_by_section(course_id, sections_names=None, assignments_names=None):
    """
    Retrieving assignments by sections.
    """
    # Retrieve the contents of the course
    sections = core_course_get_contents(course_id)

    if sections_names is not None:
        # Filter out section names
        sections = [
            section for section in sections if section["name"] in sections_names
        ]

        found_sections = set(section["name"] for section in sections)
        missing_sections = set(sections_names).difference(found_sections)

        if missing_sections:
            logger.error(
                "Could not find the following sections: %s", list(missing_sections)
            )

    if assignments_names is not None:
        # Handle missing assignments
        found_assignments = set(
            [module["name"] for section in sections for module in section["modules"]]
        )

        missing_assignments = set(assignments_names).difference(found_assignments)
        if missing_assignments:
            logger.error(
                "Could not find the following assignments: %s", missing_assignments
            )

    assignment_id_to_section = {}

    # Looking through the course contents trying to locate the assignment
    for section in sections:
        for module in section["modules"]:
            # Filter only assignments in moodle
            if module["modname"] != "assign":
                continue

            # Filter assignments by name
            if assignments_names and module["name"] not in assignments_names:
                continue

            assignment_id_to_section[module["id"]] = section["name"]

    assignments = get_assignments(course_id, list(assignment_id_to_section.keys()))
    assignments_by_section = defaultdict(list)

    for assignment in assignments:
        section_name = assignment_id_to_section[assignment.cmid]
        assignments_by_section[section_name].append(assignment)

    return assignments_by_section


def get_exercises_by_topic(courseid: int) -> Dict[str, List[Dict[str, int | str]]]:
    """
    Retrieves the LTI exercises and assignments for a given course by topic.

    Return Example:
    {
        "Topic 1": {"id": 1, "name": "Assignment 1", "type": "assign"},
        "Topic 2": {"id": 2, "name": "LTI 1", "type": "lti"},
    }
    """
    course_content = core_course_get_contents(courseid)
    course_exercises = {}
    for section in course_content:
        # Ignore topics with no exercises
        if not section["modules"]:
            continue

        # Save assignments or LTI exercises only
        section_exercises = [
            {
                "id": module["instance"],
                "name": module["name"],
                "type": module["modname"],
            }
            for module in section["modules"]
            if module["modname"] in ["assign", "lti"]
        ]

        if section_exercises:
            course_exercises[section["name"]] = section_exercises

    return course_exercises


def get_exercises(courseid: int) -> List[Dict[str, int | str]]:
    """
    Retrieves the LTI exercises and assignments for a given course in order.

    Returns an ordered list of dictionaries that contains
    - "id": ID of exercise in the LMS
    - "name": Name of exercise
    - "type": Type of exercise ("assign" | "lti")

    Example:
    [
        {"id": 1, "name": "Assignment 1", "type": "assign"},
        {"id": 2, "name": "LTI 1", "type": "lti"},
    ]
    """
    exercises_by_topic = get_exercises_by_topic(courseid)
    return [
        exercise
        for topic in exercises_by_topic
        for exercise in exercises_by_topic[topic]
    ]
