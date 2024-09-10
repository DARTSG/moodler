from collections import defaultdict

from moodler.moodle_api import call_moodle_api


def get_course_exercises(courseid: int):
    """
    Retrieve IDs of LTI exercises and assignments mapped to their name

    {
        "assign": {
            1: 'Assignment 1', 2: 'Assignment 2',
        },
        "lti": {
            3: 'LTI 1', 4: 'LTI 2',
        }
    }
    """
    course_content = call_moodle_api("core_course_get_contents", courseid=courseid)
    exercise_map = defaultdict(dict, order=[])
    for section in course_content:
        if not section["modules"]:
            continue

        for module in section["modules"]:
            if module["modname"] in ["assign", "lti"]:
                exercise_map[module["modname"]][module["instance"]] = module["name"]
                exercise_map["order"].append(module["instance"])
    
    return dict(exercise_map)
