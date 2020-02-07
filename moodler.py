"""
Two main actions so far - prints how many ungraded exercises there are
and downloads student submissions

To use, you need to create a web service user and enroll it in the module
Follow the instructions at http://<MOODLE IP>/admin/category.php?category=webservicesettings

The moodle API documentation can be found at http://192.168.10.158/admin/webservice/documentation.php

After following the instructions and enrolling the new user, edit the following variables below:
TOKEN
URL

Ooh, and use python3 to run this
and install requests package
"""

import requests
from pathlib import Path
import urllib.request
import argparse


TOKEN = '53e2cd85d463774b6b4dc67e485ca61e'
URL = 'http://192.168.10.158'
REQUEST_FORMAT = '{}/webservice/rest/server.php?wstoken={}&wsfunction={}&moodlewsrestformat=json'.format(
    URL, TOKEN, '{}')


def flatten(list_of_lists):
    flat_list = []
    for sublist in list_of_lists:
        for item in sublist:
            flat_list.append(item)
    return flat_list


def list_students():
    """
    Returns a map linking the id of all users to their full name
    """
    response = requests.get(REQUEST_FORMAT.format('core_user_get_users')
                            + '&criteria[0][key]=email&criteria[0][value]=%%')

    # Create users map
    users_map = {}
    for user in response.json()['users']:
        users_map[user['id']] = user['firstname'] + ' ' + user['lastname']
    return users_map


def courses():
    """
    Returns a tuple of ids and course names
    """
    response = requests.get(REQUEST_FORMAT.format('core_course_get_courses'))
    return response.json()


def assignments(course_id):
    """
    Returns a dictionary mapping assignment id to its name from a specified course
    """
    response = requests.get(
        REQUEST_FORMAT.format('mod_assign_get_assignments') + '&courseids[0]={}'.format(course_id))
    assigns = {}
    for assign in response.json()["courses"][0]["assignments"]:
        assigns[assign['id']] = assign['name']
    return assigns


def submissions(assignment_ids):
    """
    Returns the submissions for the given assignments in a dict
    mapping assignment id to submissions
    {id: [..]}
    """

    url = REQUEST_FORMAT.format('mod_assign_get_submissions')
    for i, assignment_id in enumerate(assignment_ids):
        url += '&assignmentids[{}]={}'.format(i, assignment_id)
    response = requests.get(url)
    subs = {}
    for assign in response.json()['assignments']:
        subs[assign['assignmentid']] = assign['submissions']
    return subs


def ungraded_submissions(course_id, verbose=False):
    """
    Returns the amount of ungraded exercises give a course id
    """
    assigns = assignments(course_id)
    names = set()

    ungraded = 0
    for assign_id, subs in submissions(assigns.keys()).items():
        for submission in subs:
            if 'submitted' == submission['status'] \
               and 'notgraded' == submission['gradingstatus']:
                ungraded += 1
                names.add(assigns[assign_id])

    if verbose:
        for name in names:
            print(name)
    return ungraded


def download_submissions(course_id, folder, download_all=False):
    """
    Downloads all the submissions from a specific course into a folder
    """
    assigns = assignments(course_id)
    users_map = list_students()
    for assign_id, subs in submissions(assigns.keys()).items():
        for submission in subs:
            # Skip ungraded
            if not 'submitted' == submission['status']:
                continue
            if not download_all and not 'notgraded' == submission['gradingstatus']:
                continue

            for plugin in submission['plugins']:
                if plugin['type'] == 'file':
                    for filearea in plugin['fileareas']:
                        for attachment in filearea['files']:
                            # Create subfolders
                            submission_folder = Path(folder) \
                                                / Path(assigns[assign_id]) \
                                                / Path(users_map[submission['userid']])
                            submission_folder.mkdir(parents=True, exist_ok=True)

                            # Download the file
                            url = attachment['fileurl']
                            file_path = submission_folder / Path(url.split('/')[-1])
                            urllib.request.urlretrieve('{}?token={}'.format(url, TOKEN),
                                                       file_path.as_posix())


def main():
    parser = argparse.ArgumentParser()
    parser.set_defaults(which='none')
    subparsers = parser.add_subparsers()

    parser_ungraded = subparsers.add_parser('ungraded',
                                            help='Prints the amount of ungraded submissions')
    parser_ungraded.add_argument('course_id', type=int, help='The course id to query')
    parser_ungraded.add_argument('--verbose', '-v', action='store_true',
                                 help='Prints the names of the ungraded exercises')
    parser_ungraded.set_defaults(which='ungraded')

    parser_download = subparsers.add_parser('download',
                                            help='download submissions to local folder')
    parser_download.add_argument('course_id', type=int, help='The course id to query')
    parser_download.add_argument('folder', type=str,
                                 help='The folder to download the submissions to')
    parser_download.add_argument('--all', action='store_true',
                                 help='If specified will download all course submissions')
    parser_download.set_defaults(which='download')

    args = parser.parse_args()

    if 'none' == args.which:
        parser.print_help()
    elif 'ungraded' == args.which:
        print("Ungraded: {}".format(ungraded_submissions(args.course_id, verbose=args.verbose)))
    elif 'download' == args.which:
        download_submissions(args.course_id, args.folder, args.all)

if '__main__' == __name__:
    main()
