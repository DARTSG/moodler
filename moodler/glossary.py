from typing import List, Dict, Union
from moodle_api import call_moodle_api
from moodle_exception import MoodlerException


class GlossaryException(MoodlerException):
    pass


class NoCourseGlossary(GlossaryException):
    pass


class NoGlossaryEntry(GlossaryException):
    pass


def mod_glossary_get_entries_by_search(
    glossary_id: int, query: str
) -> Dict[str, Union[int, List, Dict]]:
    """
    Returns the list of entries containing the search term in query
    :param glossary_id: The ID of the glossary, which could be obtained using mod_glossary_get_glossaries_by_courses function
    :param query: The string to search within the given glossary
    """
    response = call_moodle_api(
        "mod_glossary_get_entries_by_search", id=glossary_id, query=query
    )

    if response["count"] == 0:
        raise NoGlossaryEntry(
            """Search entry for '{}' did not match any results.
            Try using another search term.\n{}""".format(
                query, response
            )
        )

    return response


def mod_glossary_get_glossaries_by_courses(courseid: int) -> Dict[str, List]:
    """
    Returns a list of glossaries for the given course in a dict
    mapping glossary id to glossary
    e.g. [{id: 1, 'name': 'Test Files', ...}]
    """
    response = call_moodle_api(
        "mod_glossary_get_glossaries_by_courses", courseids=[courseid]
    )

    if not response["glossaries"]:
        raise NoCourseGlossary(
            """There are no glossaries for this course.\n{}""".format(response)
        )

    return response
