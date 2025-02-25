import json
from os import path
from typing import Any, Generator, cast, override

from typeguard import typechecked
from z3.z3 import Bool, BoolRef, ModelRef, Optimize, Or, sat  # type: ignore[import-untyped]

from config import COURSES_FILE_NAME

##########################
### START CONFIG VARIABLES
##########################
# These will all be taken as input from the user
semester_count = 2  # Number of semester to calculate for
min_credit_per_semester = 3  # Minimum credits (inclusive)
max_credits_per_semester = 6  # Maximum credits (inclusive)
starts_as_fall = True
start_year = 2025
transferred_course_ids: list[int] = []
first_semester_junior: int | None = 1
first_semester_senior: int | None = 2
########################
### END CONFIG VARIABLES
########################


@typechecked
class RefManager:
    count: int = 0
    store: dict[BoolRef, Any] = {}

    @classmethod
    def allocate(cls, value: Any) -> BoolRef:
        # Update the count
        RefManager.count += 1

        allocated_value: BoolRef = Bool(RefManager.count)

        # Add new item to the store
        RefManager.store[allocated_value] = value
        # Return items id
        return allocated_value

    @classmethod
    def get(cls, id: BoolRef) -> Any:
        if id not in RefManager.store:
            raise KeyError(f"Cannot find id '{id}' in store")
        return RefManager.store[id]

    @classmethod
    def find(cls, value: Any, default_return: Any = -1) -> Any | None:
        for k, v in RefManager.store.items():
            if v == value:
                return k
        return default_return


# A metaclass to allow easy iteration over created courses
# https://stackoverflow.com/questions/32362148/typeerror-type-object-is-not-iterable-iterating-over-object-instances
# TODO: Technically, this might have a memory leak
@typechecked
class IterableCourse(type):
    def __iter__(cls) -> Generator["Course", Any, None]:
        yield from cls.courses.values()


@typechecked
class Course(metaclass=IterableCourse):
    courses: dict[Any, "Course"] = {}
    semester_count: int = 0

    @classmethod
    def by_id(cls, id: Any) -> "Course":
        if id not in cls.courses:
            raise IndexError(f"Unable to find id '{id} in courses")
        return cls.courses[id]

    # id is received from courses and is ultimately returned
    # refs tracks location in boolean expression/which semester a class is taken
    def __init__(
        self,
        name: str,
        id: Any,
        credits: int,
        requirements: Any,
        season: Any,  # TODO: Deal with this
        credits_repeatable_for: int | None = None,
    ):
        self._name: str = name
        self._id: Any = id
        self._requirements: Any = requirements
        self._credits: int = credits
        self._credits_repeatable_for: int | None = credits_repeatable_for
        self._refs: list[BoolRef] = []
        for _ in range(Course.semester_count + 1):  # +1 because allows a slot for transfer credits
            self._refs.append(RefManager.allocate(self))

        if self._id in Course.courses:
            raise KeyError(f"Key {self._id} already exists in course list")

        Course.courses[self._id] = self

    def get_refs(self) -> list[BoolRef]:
        return self._refs

    def get_credits(self) -> int:
        return self._credits

    def at(self, start_semester: int, end_semester: int | None = None) -> BoolRef:
        if start_semester < 0 or start_semester > Course.semester_count:
            raise ValueError(f"Cannot check for rank {self._name} during semester starting below 0 (transfers) or above {Course.semester_count}")

        if end_semester is None:
            return self._refs[start_semester]

        if end_semester < 0 or end_semester > Course.semester_count:
            raise ValueError(f"Cannot check for rank {self._name} during semester ending below 0 (transfers) or above {Course.semester_count}")
        if end_semester < start_semester:
            raise ValueError(f"Cannot check for rank {self._name} with end semester before start semester")

        formula = Or(*self._refs[start_semester : end_semester + 1])
        if not isinstance(formula, BoolRef):
            raise TypeError("Expected id at semester to be a BoolRef")
        return formula

    def __str__(self) -> str:
        return f"{self._id}:{self._name}:{','.join([str(x) for x in self._refs])}"


@typechecked
class CourseSATSolver:
    def __init__(
        self,
        semester_count: int,
        min_credit_per_semester: int,
        max_credits_per_semester: int,
    ):
        Course.semester_count = semester_count
        self.courses: list[Course] = load_courses(COURSES_FILE_NAME)
        self.min_credits_per_semester: int = min_credit_per_semester
        self.max_credits_per_semester: int = max_credits_per_semester
        self.plan: list[list[Course]] | None = None

        for course_id in transferred_course_ids:
            if not Course.by_id(course_id):
                raise Exception(f"Attempting to transfer an invalid course id '{course_id}'.")

    def setup(self) -> None:
        self.solver = Optimize()

        for course in Course:
            print(course)

    def add_degree_reqs(self) -> None:
        self.solver.add(Or(Course.by_id(2).get_refs()))
        self.solver.add(Or(Course.by_id(3).get_refs()))
        self.solver.add(Or(Course.by_id(4).get_refs()))

    def minimize(self) -> None:
        refs = []
        for course in Course.courses.values():
            refs.extend(course.get_refs())

        self.solver.maximize(sum(refs))

    def solve(self) -> None:
        self.plan = [[] for _ in range(semester_count + 1)]  # TODO: Fix the semester count here

        for k, v in RefManager.store.items():
            print(f"{k}: {v}")

        if self.solver.check() == sat:
            print("SAT")
            model: ModelRef = self.solver.model()

            for funcDeclRef in model.decls():
                boolRef: BoolRef = funcDeclRef()
                if not isinstance(boolRef, BoolRef):
                    raise TypeError(f"Expected model to only consist of BoolRefs, instead got '{funcDeclRef}'")

                course: Course = RefManager.get(boolRef)
                semester: int = course.get_refs().index(boolRef)

                if model[boolRef]:
                    self.plan[semester].append(course)

        else:
            print("UNSAT")

    def display(self) -> None:
        if self.plan is None:
            raise ValueError("CourseSATSolver needs to be solver before a plan can be displayed")

        for i, semester in enumerate(self.plan):
            print(f"Semester {i}:")
            for course in semester:
                print(f"\t{course}")


def load_courses(file_name: str) -> list[Course]:
    with open(file_name, "r") as file:
        raw_courses = json.load(file)["courses"]

    return [Course(**course) for course in raw_courses]


if __name__ == "__main__":
    c: CourseSATSolver = CourseSATSolver(
        semester_count,
        min_credit_per_semester,
        max_credits_per_semester,
    )

    c.setup()
    c.add_degree_reqs()
    c.minimize()
    c.solve()
    c.display()
