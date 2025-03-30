import os

# Name of the directory containing data files
DATA_DIR: str = "data"
# Name of the file containing course data
COURSES_FILE_NAME: str = os.path.join(DATA_DIR, "minimal-cs-courses.json")
# Name of the file containing degree data
DEGREES_FILE_NAME: str = os.path.join(DATA_DIR, "simple-cs-degrees.json")
