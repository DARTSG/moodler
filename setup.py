from setuptools import setup, find_packages

NAME = "moodler"
VERSION = "1.0.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

with open("requirements.txt") as f:
    requirements = f.read().splitlines()


setup(
    name=NAME,
    version=VERSION,
    description="Moodle API wrapper for instructors",
    author_email="",
    url="",
    keywords=["Moodle API", "Education"],
    install_requires=requirements,
    packages=find_packages(),
    include_package_data=True,
    long_description="""\
    Moodle API wrapper for instructors
    """,
)
