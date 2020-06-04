# Moodler
A library that allows easy interaction with moodle.

Current features are:
* Tracking ungraded exercises for a course
* Downloading student submissions
* Exporting student grades for a given course
* Listing students enrolled in a course
* Exporting student feedbacks

This library can be used both as a library by importing the relavent modules and by running the `moodler.py` file.

Works and tested with python 3.7.7

## Setup
1. Install the requirements file `pip install -r requirements.txt`
2. Create you .env file (see example in the file `env_example`)

## Usage
`python moodler.py ungraded <course_id> [--verbose] [download_folder]`
Prints the information about ungraded exercises for a course
course_id - The id of the course to query
download_folder - if specified, will download the ungraded submissions to the given folder

`python moodler.py feedbacks <course_id> <download_folder>`
Downloads all the feedbacks from the given course to the specified folder

`python export <course_id> <download_folder>`
Exports submissions, materials, and grades for a course

`python list_students <course_id>`
List names of all students


## Useful Links
[http://<moodleip>/admin/webservice/documentation.php](Documentation for all api functions)

[http://<moodleip>/admin/webservice/service_functions.php?id=4](Allow the use of specific functions)
