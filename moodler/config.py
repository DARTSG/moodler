from environs import Env

env = Env()
env.read_env()

TOKEN = env("TOKEN")
URL = env("URL")
LOGIN_PAGE = "login/index.php"

MOODLE_USERNAME = env("MOODLE_USERNAME")
MOODLE_PASSWORD = env("MOODLE_PASSWORD")

# List of names of students to not grade
STUDENTS_TO_IGNORE = env.dict("STUDENTS_TO_IGNORE", subcast_key=int, default={})
