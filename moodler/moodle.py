import logging

import requests
from pathlib import Path
import urllib.request

from requests.auth import HTTPBasicAuth

from moodler.config import URL, USER_MAP, STUDENTS_TO_IGNORE
from moodler.consts import REQUEST_FORMAT
from moodler.download import download_file
from moodler.students import core_course_get_contents

logger = logging.getLogger(__name__)

ASSIGNMENT_WORKSHEET_EXT = '.csv'
ASSIGNMENT_ALL_SUBMISSIONS_EXT = '.zip'


# def get_assignments(course_id, assignment_ids=None):
#     """
#     Returns the ids and assignment names from a specific course
#
#     :param course_id: The ID of the course to retrieve its assignments
#     :param assignment_ids: Specific assignment IDs to retrieve.
#     """
#     response = requests.get(
#         REQUEST_FORMAT.format('mod_assign_get_assignments') + '&courseids[0]={}'.format(course_id))
#     assignments = response.json()["courses"][0]["assignments"]
#
#     # Filter specific assignment IDs
#     if assignment_ids:
#         assignments = [assignment for assignment in assignments if assignment['cmid'] in assignment_ids]
#
#     return assignments


# def get_submissions(assignment_id):
#     """
#     Returns the submissions for a given assignment
#     TODO: Too slow... make this accept multiple assignment ids
#     """
#     response = requests.get(
#         REQUEST_FORMAT.format('mod_assign_get_submissions') + '&assignmentids[0]={}'.format(
#             assignment_id))
#     return response.json()['assignments'][0]['submissions']


def download_all_submissions(assignment_id,
                             assignment_name,
                             output_path,
                             session=SESSION):
    """
    Download all submissions ZIP from the Moodle using the session created.
    :param assignment_id: The ID of the submission to download.
    :param assignment_name: The name of the assignment to use for the name of
    the ZIP downloaded from Moodle.
    :param output_path: The path in which to saved the downloaded file.
    :param session: The session through which to send the get request to
    download the file.
    :return:
    """
    # TODO: doesn't work yet, have to develop a web service that does this
    # Build the get request.
    params = {
        'id': assignment_id,
        'action': 'downloadall'
    }
    response = session.get(URL + '/mod/assign/view.php', params=params)

    # TODO: Raise an exception in case the file download failed

    all_submissions_file_name = \
        Path(output_path) / Path(assignment_name + ASSIGNMENT_ALL_SUBMISSIONS_EXT)

    # Writing the content from the get response into a file.
    with all_submissions_file_name.open(mode='wb') as all_submissions_file:
        all_submissions_file.write(response.content)

    return all_submissions_file_name


def download_grading_worksheet(assignment_id,
                               assignment_name,
                               output_path,
                               session=SESSION):
    """
    Download the grading sheet from the Moodle using the session created.
    :param assignment_id: The ID of the grading sheet to download.
    :param assignment_name: The name of the assignment to use for the name of
    the grading sheet.
    :param output_path: The path in which to saved the downloaded file.
    :param session: The session through which to send the get request to
    download the file.
    :return:
    """
    # TODO: doesn't work yet, have to develop a web service that does this
    params = {
        'id': assignment_id,
        'plugin': 'offline',
        'pluginsubtype': 'assignfeedback',
        'action': 'viewpluginpage',
        'pluginaction': 'downloadgrades'
    }
    response = session.get(URL + '/mod/assign/view.php', params=params)

    # TODO: Raise an exception in case the file download failed

    grading_worksheet_file_name = \
        Path(output_path) / Path(assignment_name + ASSIGNMENT_WORKSHEET_EXT)

    with grading_worksheet_file_name.open(mode='wb') as grading_worksheet_file:
        grading_worksheet_file.write(response.content)

    return grading_worksheet_file_name


def get_assignments_details(course_id, assignments_list):
    """
    Returns a dictionary with a tuple for every assignment name in the list
    received that looks like this: (assignment_id, assignment_section)
    :param course_id: The ID of the course to retrieve the assigments from.
    :param assignments_list: List of assignments names to retrieve their data.
    :return: Dictionary of (assignment_id, assignment_section) for every
    assignment.
    """
    # TODO: What's this needed for? Not sure, it's unused.
    assignments_dict = {}

    # Retrieve the contents of the course
    sections = core_course_get_contents(course_id)

    # Looking through the course contents trying to locate the assignment
    for section in sections:
        for module in section['modules']:
            # We are only looking for assignments and no other resource in
            # the moodle
            if module['modname'] != 'assign':
                continue

            # Looking only for an exercise in the received list
            if module['name'] not in assignments_list:
                continue

            # Retrieve all the assignment files
            assignment_files = get_assignment_files(module['id'])

            # Adding the results to the dictionary of assignments we are
            # crafting for the caller
            assignments_dict[module['name']] = (module['id'],
                                                section['name'],
                                                assignment_files)

    return assignments_dict


def ungraded_submissions(course_id, is_verbose, download_folder=None):
    """
    Returns the amount of ungraded exercises give a course id

    :param is_verbose: True if output should contain all students ignored, False for totals only.

    Note:
        - Can't differentiate between new submissions and resubmissions via the
        API, so we only count new submissions.
        -
    """
    logger.info("Showing ungraded submissions for course %s", course_id)
    total_ungraded = 0
    for assignment in get_assignments(course_id):
        ungraded = 0
        # List of student names whose submissions were ignored
        ungraded_ignored = []
        submissions = get_submissions(assignment['id'])
        # Count total number of submissions to this exercise
        total_submissions = 0
        for submission in submissions:
            if 'submitted' == submission['status']:
                total_submissions += 1

                # Already graded, at least once
                if 'notgraded' != submission['gradingstatus']:
                    continue

                # Process ungraded submission
                student_id = submission['userid']
                if student_id in STUDENTS_TO_IGNORE.keys():
                    ungraded_ignored.append(STUDENTS_TO_IGNORE[student_id])
                else:
                    ungraded += 1
            # TODO: Improve with 'attemptnumber' field, to check "== 0" for new submissions only, or resubmissions
        if is_verbose and len(ungraded_ignored) != 0:
            logger.info("Ignored %s submissions for assignment '%s' (CMID %s, ID %s): %s", len(ungraded_ignored),
                        assignment['name'], assignment['cmid'], assignment['id'], ungraded_ignored)
        if ungraded != 0:
            logger.info("Total ungraded for assignment '%s' (CMID %s, ID %s): %s/%s", assignment['name'],
                        assignment['cmid'], assignment['id'], ungraded, total_submissions)
        total_ungraded += ungraded
    return total_ungraded


def download_submissions(download_folder, course_id=None, assignment_ids=None, download_all=False):
    """
    Download all the submissions from a given course ID, or specific assignments, into a local folder.

    :param course_id: If assignment_ids were specified as well, download submissions for those only. If course_id was
    specified, download submissions for all assignments in that course.
    :param assignment_ids: If specified, download only the given assignment IDs for the course.
    :param download_all: True if all submissions should be downloaded, False if only ones that haven't been graded yet
    should be downloaded.
    """
    # if course_id is None and assignment_ids is None:
    #     raise Exception("Either course_id or assignment_ids must be defined")
    logger.info("Downloading submissions in course %s", course_id)

    # Select specific assignment IDs to download
    assignment_ids_to_download = get_assignments(course_id, assignment_ids=assignment_ids)

    # Download submissions
    priority_counter = 1
    for assignment in assignment_ids_to_download:
        logger.info("Assignment #%s: %s", priority_counter, assignment['name'])
        submissions = get_submissions(assignment['id'])

        # Flag to mark if any submissions were downloaded
        are_any_submissions = False
        for submission in submissions:
            # Skip ungraded
            if submission['status'] != 'submitted':
                continue
            if not download_all and submission['gradingstatus'] != 'notgraded':
                continue

            are_any_submissions = True
            download_submission(assignment['name'], None, submission, download_folder)

        # Download intro files
        if are_any_submissions:
            for intro_attachment in assignment['introattachments']:
                assignment_folder = generate_assignment_folder_path(assignment['name'], download_folder)
                download_file(intro_attachment['fileurl'], assignment_folder)

        priority_counter += 1


def list_students():
    response = requests.get(
        REQUEST_FORMAT.format('core_user_get_users') + '&criteria[0][key]=email&criteria[0][value]=%%')

    # Create users map
    users_map = {}
    for user in response.json()['users']:
        users_map[user['id']] = user['firstname'] + ' ' + user['lastname']
    return users_map


def connect_to_server(username, password):
    """
    Function to connect to the
    :param username:
    :param password:
    :return:
    """
    session = requests.Session()

    params = {
        'anchor': '',
        'logintoken': '6932c6a583c1200d303d97109e4d7fec', # TODO: Understand this field
        'username': username,
        'password': password
    }

    session.post('http://192.168.1.55/login/index.php', params=params)

    # TODO: Check if the login has succeeded

    return session
