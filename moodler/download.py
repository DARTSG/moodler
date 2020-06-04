from pathlib import Path
import urllib.request

from moodler.config import TOKEN, URL


ASSIGNMENT_WORKSHEET_EXT = '.csv'
ASSIGNMENT_ALL_SUBMISSIONS_EXT = '.zip'


def download_file(url, folder):
    file_name = url.split('/')[-1]
    if -1 != file_name.find('?'):
        file_name = file_name.split('?')[0]
    file_path = Path(folder) / Path(file_name)
    urllib.request.urlretrieve('{}?token={}'.format(url, TOKEN), file_path.as_posix())


def generate_assignment_folder_path(assignment_name, username, download_folder, priority=None):
    # Prepare name for assignment folder
    assignment_folder_name = assignment_name
    if priority:
        assignment_folder_name = str(priority) + "--" + assignment_name

    # Create sub-folder for assignment
    submission_folder = Path(download_folder) \
                        / Path(assignment_folder_name) \
                        / Path(username)
    return submission_folder


def download_submission(assignment_name, username, submission, download_folder, priority=None):
    """
    Download the given submission, while creating the appropriate subfolders
    """
    # Create subfolders
    submission_folder = generate_assignment_folder_path(assignment_name, username, download_folder, priority)

    submission_folder.mkdir(parents=True, exist_ok=True)

    for sf in submission.submission_files:
        # Download the file
        download_file(sf.url, submission_folder)


def download_all_submissions(assignment_id,
                             assignment_name,
                             output_path,
                             session):
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
                               session):
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
