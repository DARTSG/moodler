import csv
from pathlib import Path

from moodler.moodle_api import call_moodle_api


class Feedback(object):
    def __init__(self, uid, name, answers_json):
        self.uid = uid
        self.name = name
        self.responses_count = answers_json['completedcount']
        self.questions = set()

        self.responses = [[] for i in range(self.responses_count)]

        for question in answers_json['itemsdata']:
            self.questions.add(question['item']['name'])
            for i, answer in enumerate(question['data']):
                self.responses[i].append(answer)

    def __repr__(self):
        return 'Feedback(uid={}, name={}, answers={})'.format(self.uid, self.name, self.responses_count)


def mod_feedback_get_feedbacks_by_courses(course_id):
    """
    Retrieves all feedbacks for a given course
    """
    response = call_moodle_api('mod_feedback_get_feedbacks_by_courses',
                               courseids=[course_id])

    return response['feedbacks']


def mod_feedback_get_analysis(feedback_id):
    """
    Retrieves the responses for the given feedback id
    """
    response = call_moodle_api('mod_feedback_get_analysis',
                               feedbackid=feedback_id)

    return response


def feedbacks(course_id):
    """
    Retrieve the feedbacks for a given course
    """
    fbs = []
    for feedback in mod_feedback_get_feedbacks_by_courses(course_id):
        answers = mod_feedback_get_analysis(feedback['id'])
        fbs.append(Feedback(feedback['id'], feedback['name'], answers))
    return fbs
