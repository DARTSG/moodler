# Moodler

A library that allows easy interaction with moodle.

Current features are:

* Tracking ungraded exercises for a course
* Downloading student submissions
* Exporting student grades for a given course
* Listing students enrolled in a course
* Exporting student feedbacks

This library can be used both as a library by importing the relavent modules and by running the `main.py` file.

Works and tested with python 3.7.7

## Setup

### Setup Moodle

To use, you need to create a web service user and enroll it in the module
Follow the instructions at http://<MOODLE IP>/admin/category.php?category=webservicesettings

Add the following functions:
    mod_feedback_get_analysis
    mod_feedback_get_feedbacks_by_courses
    mod_assign_get_grades
    mod_assign_get_submissions
    mod_assign_get_assignments
    core_enrol_get_enrolled_users
    core_course_get_courses
    mod_glossary_get_glossaries_by_courses
    mod_glossary_get_entries_by_search

The moodle API documentation can be found at http://192.168.10.158/admin/webservice/documentation.php

### Setup repo

1. Install the requirements file `pip install -r requirements.txt`
2. Create you .env file (see example in the file `dotenv_example`)
3. Extract the token for the .env file from this URL: `http://moodleip/admin/settings.php?section=webservicetokens`
4. Enroll the `moodle` user the the relevant course.

## Usage

```bash
python main.py ungraded <course_id> [--verbose] [download_folder]
```

Prints the information about ungraded exercises for a course
course_id - The id of the course to query
download_folder - if specified, will download the ungraded submissions to the given folder

```bash
python main.py feedbacks <course_id> <download_folder>
```

Downloads all the feedbacks from the given course to the specified folder

```bash
python main.py export <course_id> <download_folder>
```

Exports submissions, materials, and grades for a course

```bash
python main.py list_students <course_id>
```

List names of all students

## Useful Links

`http://<moodleip>/admin/webservice/documentation.php` - Documentation for all api functions

`http://<moodleip>/admin/webservice/service_functions.php?id=4` - Allow the use of specific functions

