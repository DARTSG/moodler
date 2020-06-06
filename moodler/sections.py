import logging
import requests

from moodler.consts import REQUEST_FORMAT
from moodler.assignment import get_assignments

logger = logging.getLogger(__name__)


# Exceptions for the current module ###
class SectionsException(Exception):
    pass


class EmptyCoursesList(SectionsException):
    pass


class InvalidCourseName(SectionsException):
    pass


class CoursePrefixNotFound(SectionsException):
    pass


class CourseNotFoundInMoodle(SectionsException):
    pass


class Course(object):
    def __init__(self, course_id, full_name, short_name):
        self.id = course_id
        self.full_name = full_name
        self.short_name = short_name

    def __repr__(self):
        return 'Course(courde_id={}, full_name={}, short_name={})'.format(
            self.id,
            self.full_name,
            self.short_name)


def core_course_get_courses():
    """
    Returns a tuple of ids and course names
    """
    response = requests.get(REQUEST_FORMAT.format('core_course_get_courses'))
    return response.json()


def core_course_get_contents(course_id):
    """
    Returns the structure of the course with all resources and topics
    """
    return requests.get(REQUEST_FORMAT.format('core_course_get_contents')
                        + '&courseid={}'.format(course_id)).json()


def list_courses(course_prefix=None):
    """
    Create a list of all the courses in the moodle that contain the course
    prefix received. If the prefix is None, list all courses in the Moodle.
    :param course_prefix: The prefix that the courses should contain. If not
    received, list all courses in the Moodle.
    :return: Returns a list of courses objects.
    """
    courses_list = []
    courses_from_moodle = core_course_get_courses()

    if not courses_from_moodle:
        raise EmptyCoursesList("The Moodle has returned an empty courses list")

    for course in courses_from_moodle:
        if course_prefix is not None:
            if ((course_prefix not in course['shortname']) and
                    (course_prefix not in course['fullname'])):
                continue

        courses_list.append(Course(course['id'],
                                   course['shortname'],
                                   course['fullname']))

    return courses_list


def locate_course_id(course_name, course_prefix, courses_list):
    """
    This function locates the course ID in the list of courses on the server.
    :param course_name: The name of the course (or partly its name) we want
    to locate.
    :param course_prefix: The prefix that the course name should lead with.
    :param courses_list: The list of courses in which the course name should
    appear.
    :return: Upon success, the function will return the ID of the course
    relating to the name received.
    """
    if course_name not in courses_list:
        raise InvalidCourseName("The course name '%s' is not a valid course "
                                "name. You must choose a course name from the "
                                "list in the configuration.")

    logger.info("Creating a list of all courses in the Moodle that contain "
                "the prefix '%s'",
                course_prefix)

    courses = list_courses(course_prefix)

    if not courses:
        raise CoursePrefixNotFound("No course in the Moodle was found with "
                                   "the prefix set in the configuration '%s'",
                                   course_prefix)

    for course in courses:
        if course_name in course.full_name or course_name in course.short_name:
            return course.id

    raise CourseNotFoundInMoodle("The course name you have used '%s' was not "
                                 "found in the Moodle")


def locate_course_name(course_id, course_prefix=None):
    """
    Locating the name of the course based on the ID received.
    """
    courses = list_courses()

    for course in courses:
        if course.id != course_id:
            continue

        if course_prefix is None:
            return course.full_name

        if (course_prefix in course.full_name) or \
                (course_prefix in course.short_name):
            return course.full_name.lstrip(course_prefix).strip()

        raise CoursePrefixNotFound("The course corresponding to the ID "
                                   "received does not contained the prefix "
                                   "determined.")

    raise CourseNotFoundInMoodle("No course with the ID received has been "
                                 "found in the Moodle.")


def get_assignments_by_section(course_id,
                               sections_names=None,
                               assignments_names=None):
    """
    Retrieving assignments by sections.
    """
    exercises_by_sections = {}

    # Retrieve the contents of the course
    sections = core_course_get_contents(course_id)

    if sections_names is not None:
        sections_not_found = sections_names[:]

    # Looking through the course contents trying to locate the assignment
    for section in sections:
        # Making sure this section is one of the sections we are supposed to
        # be looking at, unless the list is None
        if sections_names is not None:
            if section['name'] not in sections_names:
                continue

        sections_not_found.remove(section['name'])

        current_section_assignments = []
        for module in section['modules']:
            # We are only looking for assignments and no other resource in
            # the moodle
            if module['modname'] != 'assign':
                continue

            # Looking only for an exercise in the received list, unless it is
            # None
            if assignments_names is not None:
                if module['name'] not in assignments_names:
                    continue

            current_section_assignments.append(module['id'])

        if current_section_assignments:
            exercises_by_sections[section['name']] = get_assignments(
                current_section_assignments)

    if sections_not_found:
        logger.error("Could not find the following sections: %s",
                     sections_not_found)

    return exercises_by_sections
