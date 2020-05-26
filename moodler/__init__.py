from moodler.moodle import connect_to_server
from moodler.config import USERNAME, PASSWORD

SESSION = connect_to_server(USERNAME, PASSWORD)
