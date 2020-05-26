from moodler.moodle_connect import connect_to_server
from moodler.config import USERNAME, PASSWORD

__all__ = ["SESSION"]

SESSION = connect_to_server(USERNAME, PASSWORD)
