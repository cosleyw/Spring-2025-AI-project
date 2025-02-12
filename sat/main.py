from typing import Any, override
import json
from z3 import Bool, Solver
from typeguard import check_type, typechecked

##########################
### START CONFIG VARIABLES
##########################
semester_count = 3  # Number of semester to calculate for
########################
### END CONFIG VARIABLES
########################


class Course:
    courses: dict[Any, "Course"] = {}

    @classmethod
    def by_id(cls, id: Any) -> "Course":
        return cls.courses[id]

    def __init__(self, name: str, id: Any):
        self.name: str = name
        self.id: Any = id

        if self.id in Course.courses:
            raise KeyError(f"Key {self.id} already exists in course list")

        Course.courses[self.id] = self

    @override
    def __str__(self) -> str:
        return f"<Course name={self.name} id={self.id}>"


def load_classes(file_name: str) -> list[Course]:
    with open(file_name, "r") as file:
        # TODO: Add some validation for the input file when the structure is fully figured out
        raw_courses = json.load(file)["courses"]

    return [Course(**course) for course in raw_courses]


if __name__ == "__main__":
    courses = load_classes("courses.json")
    for course in courses:
        print(course)

    print(Course.by_id(3))
