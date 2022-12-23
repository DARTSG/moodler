import logging
import os
import re
from enum import Enum
from typing import Tuple

import requests

from moodler.assignment import Assignment
from moodler.config import URL
from moodler.moodle_exception import MoodlerException

logger = logging.getLogger(__name__)


class ContentType(Enum):
    Excel = "application/vnd.ms-excel"


class UploadException(MoodlerException):
    pass


class InvalidGradingPage(UploadException):
    pass


class InvalidUploadGradingWorksheetPage(UploadException):
    pass


class InvalidUploadGradingConfirmationPage(UploadException):
    pass


def get_params_from_grading_page(assignment_id: str, session: requests.Session) -> Tuple[str, str]:
    """
    Getting contextid and sesskey parameters needed for the upload worksheet requests
    :return: A tuple of contextid and sesskey parameters.
    """
    # Build the get request to the grading page.
    params = {"id": assignment_id, "action": "grading"}
    response = session.get(URL + "/mod/assign/view.php", params=params)

    grading_page_content = response.text
    contextid_match = re.search(
        r'<input name="contextid" type="hidden" value="(\d+)"', grading_page_content
    )
    sesskey_match = re.search(
        r'<input name="sesskey" type="hidden" value="([\w\d]+)"', grading_page_content
    )

    if contextid_match is None:
        raise InvalidGradingPage(
            "The contextid required to upload the " "grading sheet to moodle was not found."
        )
    if sesskey_match is None:
        raise InvalidGradingPage(
            "The sesskey required to upload the " "grading sheet to moodle was not found."
        )
    return contextid_match.group(1), sesskey_match.group(1)


def get_params_from_upload_grading_worksheet_page(
    assignment_id: str, session: requests.Session
) -> str:
    # Build the get request to the upload grading worksheet page.
    params = {
        "id": assignment_id,
        "plugin": "offline",
        "pluginsubtype": "assignfeedback",
        "action": "viewpluginpage",
        "pluginaction": "uploadgrades",
    }
    response = session.get(URL + "/mod/assign/view.php", params=params)

    upload_grading_worksheet_page_content = response.text
    gradesfile_match = re.search(
        r'<input type="hidden" name="gradesfile" id="id_gradesfile" value="(\d+)"',
        upload_grading_worksheet_page_content,
    )

    if gradesfile_match is None:
        raise InvalidUploadGradingWorksheetPage(
            "The gradesfile required to upload the " "grading sheet to moodle was not found."
        )
    return gradesfile_match.group(1)


def upload_file_to_moodle(
    file_path: str,
    content_type: ContentType,
    contextid: str,
    sesskey: str,
    gradesfile: str,
    session: requests.Session,
):
    # Build the post request to upload the grading worksheet.
    file_name = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        file_content = f.read()

    multipart_params = {
        "repo_upload_file": (file_name, file_content, content_type.value),
        "sesskey": (None, sesskey),
        "repo_id": (None, "4"),
        "itemid": (None, gradesfile),
        "author": (None, "John Doe"),
        "title": (None, file_name),
        "ctx_id": (None, contextid),
    }

    params = {"action": "upload"}
    session.post(URL + "/repository/repository_ajax.php", params=params, files=multipart_params)


def get_params_from_submitting_uploaded_grading_worksheet(
    assignment_id: str, sesskey: str, gradesfile: str, session: requests.Session
) -> Tuple[str, str]:
    """
    Getting importid and draftid parameters needed for the upload worksheet requests
    :return: A tuple of importid and draftid parameters.
    """
    # Build the post request to submit the uploaded the grading worksheet.
    data = {
        "id": assignment_id,
        "action": "viewpluginpage",
        "pluginaction": "uploadgrades",
        "plugin": "offline",
        "pluginsubtype": "assignfeedback",
        "sesskey": sesskey,
        "_qf__assignfeedback_offline_upload_grades_form": "1",
        "mform_isexpanded_id_uploadgrades": "1",
        "gradesfile": gradesfile,
        "encoding": "UTF-8",
        "separator": "comma",
        "submitbutton": "Upload+grading+worksheet",
    }
    response = session.post(URL + "/mod/assign/view.php", data=data)

    confirmation_page_content = response.text
    importid_match = re.search(
        r'<input name="importid" type="hidden" value="(\d+)"', confirmation_page_content
    )
    draftid_match = re.search(
        r'<input name="draftid" type="hidden" value="(\d+)"', confirmation_page_content
    )

    if importid_match is None:
        raise InvalidUploadGradingConfirmationPage(
            "The importid required to upload the " "grading sheet to moodle was not found."
        )
    if draftid_match is None:
        raise InvalidUploadGradingConfirmationPage(
            "The draftid required to upload the " "grading sheet to moodle was not found."
        )
    return importid_match.group(1), draftid_match.group(1)


def confirm_grading_with_uploaded_worksheet(
    assignment_id: str,
    assignment_name: str,
    sesskey: str,
    importid: str,
    draftid: str,
    session: requests.Session,
) -> int:
    """
    :return: The number of submissions that were graded
    """
    # Build the post request to confirm grading based on the uploaded the
    # grading worksheet.
    data = {
        "id": assignment_id,
        "action": "viewpluginpage",
        "confirm": "true",
        "plugin": "offline",
        "pluginsubtype": "assignfeedback",
        "pluginaction": "uploadgrades",
        "importid": importid,
        "encoding": "UTF-8",
        "separator": "comma",
        "ignoremodified": "",
        "draftid": draftid,
        "sesskey": sesskey,
        "_qf__assignfeedback_offline_import_grades_form": "1",
        "mform_isexpanded_id_importgrades": "1",
        "submitbutton": "Confirm",
    }
    response = session.post(URL + "/mod/assign/view.php", data=data)
    result_page_content = response.text
    success_match = re.search(r"Updated (\d+) grades and feedback", result_page_content)
    if success_match is None:
        raise UploadException(
            "Failed to upload grading worksheet for assignment {} (ID: {})".format(
                assignment_name, assignment_id
            )
        )

    updated_submissions_count = int(int(success_match.group(1)) / 2)
    return updated_submissions_count


def upload_grading_worksheet(
    assignment: Assignment, grading_worksheet_csv_path: str, session: requests.Session
):
    assignment_id = assignment.cmid
    assignment_name = assignment.name

    contextid, sesskey = get_params_from_grading_page(assignment_id, session)
    gradesfile = get_params_from_upload_grading_worksheet_page(assignment_id, session)
    upload_file_to_moodle(
        grading_worksheet_csv_path,
        ContentType.Excel,
        contextid,
        sesskey,
        gradesfile,
        session,
    )
    importid, draftid = get_params_from_submitting_uploaded_grading_worksheet(
        assignment_id, sesskey, gradesfile, session
    )

    updated_submissions_count = confirm_grading_with_uploaded_worksheet(
        assignment_id, assignment_name, sesskey, importid, draftid, session
    )

    logger.info(
        "Assignment {}: Updated {} grades".format(assignment_name, updated_submissions_count)
    )
