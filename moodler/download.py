import re
from pathlib import Path
import urllib.request

from moodler.config import TOKEN, URL


ASSIGNMENT_WORKSHEET_EXT = '.csv'
ASSIGNMENT_ALL_SUBMISSIONS_EXT = '.zip'
COURSE_REPORT_EXT = '.ods'

# Pattern to locate the ticks in the web page to create the report download
# request.
REPORT_TICK_ITEM_PATTERN = r'<label>\s+<input type="hidden" name="itemids\[(' \
                           r'\d+)\]".*?>\s+([\[\]0-9\-_\w ]+)\s+</label>'
REPORT_DOWNLOAD_SESSKEY_PATTERN = r'<input name="sesskey" type="hidden" ' \
                                  r'value="([\w\d]+)"'
INVALID_REPORT_DOWNLOAD_PATTERN = '<b>Warning</b>'
REPORT_OPTIONS_TO_IGNORE = ['Course total', 'Deletion in progress']
REPORT_DIGITS_AFTER_DECIMAL_POINT = 2

REPORT_FILE_NAME_FORMAT = '{} Report' + COURSE_REPORT_EXT


class DownloadException(Exception):
    pass


class InvalidReportDownloadPage(DownloadException):
    pass


class InvalidReportDownload(DownloadException):
    pass


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


def download_course_grades_report(course_id,
                                  course_name,
                                  should_export_feedback,
                                  output_path,
                                  session):
    """
    Function for downloading the course grades reports from the Moodle UI.
    This function receives the course_id, and using regex, it parses the
    report download page and posts a request with the right information for
    downloading the submissions.
    :param course_id: The ID of the course to download its report.
    :param course_name: The name of the course to download its report.
    :param should_export_feedback: Boolean flag to indicate whether the
    report should include the feedbacks.
    :param output_path: The output path in which to save the course report.
    :param session: The session through which to send the get request to
    download the file.
    """
    params = {'id': course_id}
    report_download_page_response = session.get(URL +
                                                '/grade/export/ods/index.php',
                                                params=params)

    # Decoding and retrieving the content of the download page
    download_page_content = report_download_page_response.content.decode()

    # Locate the sesskey required for downloading the report
    sesskey_match = re.search(REPORT_DOWNLOAD_SESSKEY_PATTERN,
                              download_page_content)

    # Validating that the sesskey required for the report download has been
    # found
    if sesskey_match is None:
        raise InvalidReportDownloadPage("The sesskey required to download the "
                                        "report from the moodle was not found.")

    # Locating all the ticks option required to select all exercises in the
    # course to be part of the report
    report_ticks = re.findall(REPORT_TICK_ITEM_PATTERN,
                              download_page_content,
                              re.DOTALL | re.MULTILINE)

    # Validating that the ticks for selecting the exercise in the download
    # page have been found.
    if not report_ticks:
        raise InvalidReportDownloadPage("No checkboxes for selecting "
                                        "exercises in the download page from "
                                        "the Moodle UI have been found.")

    # Building the POST request to retrieve the report file by selecting the
    # right options in the page.

    body_params = {
        'mform_isexpanded_id_gradeitems': 1,
        'checkbox_controller1': 1,
        'mform_isexpanded_id_options': 1,
        'id': course_id,
        'sesskey': sesskey_match.group(1),
        '_qf__grade_export_form': 1,
    }

    # Selecting all the exercises in the page except from the ones we want to
    # avoid
    for tick_index, tick_name in report_ticks:
        tick_option = 1

        # Validating that we are ignoring options that are set to be ignored.
        # For example, if the tick relates to a "Deletion in progress"
        # exercise, then this exercise is irrelevant and should not be set in
        # the options.
        for to_ignore in REPORT_OPTIONS_TO_IGNORE:
            if to_ignore in tick_name:
                tick_option = 0

        body_params['itemids[{}]'.format(tick_index)] = tick_option

    body_params['export_feedback'] = int(should_export_feedback)
    body_params['export_onlyactive'] = 1
    body_params['display[real]'] = 1
    body_params['display[precentage]'] = 0
    body_params['display[letter]'] = 0
    body_params['decimal'] = REPORT_DIGITS_AFTER_DECIMAL_POINT
    body_params['submitbutton'] = 'Download'

    # Executing the POST request.
    report_download_response = session.post(URL + '/grade/export/ods/export.php',
                                            data=body_params)

    report_content = report_download_response.content

    # Validating the returned report is valid.
    if INVALID_REPORT_DOWNLOAD_PATTERN in str(report_content):
        raise InvalidReportDownload('There has been a problem with the '
                                    'received parameters for the download '
                                    'POST request.')

    report_file_name = \
        Path(output_path) / Path(REPORT_FILE_NAME_FORMAT.format(course_name))

    with report_file_name.open(mode='wb') as report_file:
        report_file.write(report_content)

    return report_file_name
