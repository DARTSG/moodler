from environs import Env

env = Env()
env.read_env()

TOKEN = env('TOKEN')
URL = env('URL')
LOGIN_PAGE = 'login/index.php'

# List of names of students to not grade
STUDENTS_TO_IGNORE = env.dict('STUDENTS_TO_IGNORE', subcast_key=int, default={})
