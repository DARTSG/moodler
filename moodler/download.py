from pathlib import Path
import urllib.request

from moodler.config import TOKEN, USER_MAP


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
    # TODO: Where does username come from?
    username = USER_MAP[submission['userid']]
    # Create subfolders
    submission_folder = generate_assignment_folder_path(assignment_name, username, download_folder, priority)

    submission_folder.mkdir(parents=True, exist_ok=True)

    for sf in submission.submission_files:
        # Download the file
        download_file(sf.url, submission_folder)

