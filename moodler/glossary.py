from typing import TypedDict

from moodler.moodle_api import call_moodle_api
from moodler.moodle_exception import MoodlerException


class GlossaryException(MoodlerException):
    pass


class NoCourseGlossary(GlossaryException):
    pass


class NoGlossaryEntry(GlossaryException):
    pass


class GlossaryEntry(TypedDict):
    id: int
    glossaryid: int
    userid: int
    userfullname: str
    userpictureurl: str
    concept: str
    definition: str
    definitionformat: int
    definitiontrust: bool
    attachment: bool
    attachments: list[object]
    timecreated: int
    timemodified: int
    teacherentry: bool
    sourceglossaryid: int
    usedynalink: bool
    casesensitive: bool
    fullmatch: bool
    approved: bool
    tags: list[object]


class GlossaryEntries(TypedDict):
    count: int
    entries: list[GlossaryEntry]
    ratinginfo: dict
    warnings: list[dict]


def mod_glossary_get_entries_by_search(glossary_id: int, query: str) -> GlossaryEntries:
    """
    Returns the list of entries containing the search term in query
    :param glossary_id: The ID of the glossary, which could be obtained using mod_glossary_get_glossaries_by_courses function
    :param query: The string to search within the given glossary
    """
    response: GlossaryEntries = call_moodle_api(
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


class Glossary(TypedDict):
    id: int
    coursemodule: int
    course: int
    name: str
    intro: str
    introformat: int
    introfiles: list[object]
    section: int
    visible: bool
    groupmode: int
    groupingid: int
    lang: str
    allowduplicatedentries: int
    displayformat: str
    mainglossary: int
    showspecial: int
    showalphabet: int
    showall: int
    allowcomments: int
    allowprintview: int
    usedynalink: int
    defaultapproval: int
    approvaldisplayformat: str
    globalglossary: int
    entbypage: int
    editalways: int
    rsstype: int
    rssarticles: int
    assessed: int
    assesstimestart: int
    assesstimefinish: int
    scale: int
    timecreated: int
    timemodified: int
    completionentries: int
    browsemodes: list[str]
    canaddentry: int


class Glossaries(TypedDict):
    glossaries: list[Glossary]
    warnings: list[dict]


def mod_glossary_get_glossaries_by_courses(courseid: int) -> Glossaries:
    """
    Returns a list of glossaries for the given course in a dict
    mapping glossary id to glossary
    e.g. [{id: 1, 'name': 'Test Files', ...}]
    """
    response: Glossaries = call_moodle_api(
        "mod_glossary_get_glossaries_by_courses", courseids=[courseid]
    )

    if not response["glossaries"]:
        raise NoCourseGlossary(
            """There are no glossaries for this course.\n{}""".format(response)
        )

    return response
