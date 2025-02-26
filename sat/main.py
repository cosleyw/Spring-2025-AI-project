from enum import StrEnum
import json
from typing import Any, Generator, TypeVar, override

from typeguard import typechecked
from z3.z3 import And, Bool, BoolRef, BoolVal, ModelRef, Not, Optimize, Or, sat  # type: ignore[import-untyped]

from config import COURSES_FILE_NAME

##########################
### START CONFIG VARIABLES
##########################
# These will all be taken as input from the user
semester_count = 4  # Number of semester to calculate for
min_credit_per_semester = 6  # Minimum credits (inclusive)
max_credits_per_semester = 12  # Maximum credits (inclusive)
starts_as_fall = True
start_year = 2025
transferred_course_ids: list[str] = ["CS1410", "CS1510"]
desired_course_ids: list[str] = ["CS2150", "CS4620/5620"]
# NOTE: One-indexed!
first_semester_sophomore: int | None = 1
first_semester_junior: int | None = 1
first_semester_senior: int | None = 2
first_semester_graduate: int | None = None
first_semester_doctoral: int | None = None
########################
### END CONFIG VARIABLES
########################


@typechecked
class Offering(StrEnum):
    FALL = "FALL"
    SPRING = "SPRING"
    FALL_AND_SPRING = "FALL_AND_SPRING"
    VARIABLE = "VARIABLE"
    EVEN_FALL = "EVEN_FALL"
    ODD_FALL = "ODD_FALL"
    EVEN_SPRING = "EVEN_SPRING"
    ODD_SPRING = "ODD_SPRING"


T = TypeVar("T")


@typechecked
def rotate(lst: list[T], n: int) -> list[T]:
    return lst[-n:] + lst[:-n]


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


@typechecked
class Rank:
    # first_semester_with_rank of None is intepreted as you never become the rank
    # first_semester_with_rank of 0 is intepreted as you start with the rank
    def __init__(self, name: str, first_semester_with_rank: int | None):
        self._name: str = name
        self._first_semester_with_rank: int | None = first_semester_with_rank
        self._refs: list[BoolRef] = []
        for _ in range(semester_count):
            self._refs.append(RefManager.allocate(self))

        if (first_semester_with_rank is not None) and (first_semester_with_rank < 1 or first_semester_with_rank > semester_count):
            raise ValueError(f"Cannot start semester with rank {name} cannot be before first semester or after last semester. Set as None if never reached, and 0 is instantly reached.")

    def at(self, semester: int) -> BoolRef:
        if semester < 1 or semester > semester_count:
            raise ValueError(f"Cannot check for rank {self._name} during semester below 1 or above {semester_count}")
        return self._refs[semester - 1]

    def generate_bootstrap(self) -> list[BoolRef]:
        requirements: list[BoolRef] = []

        if self._first_semester_with_rank is None:
            offset = semester_count
        else:
            offset = self._first_semester_with_rank - 1

        for rank in self._refs[offset:]:
            requirements.append(rank)
        for not_rank in self._refs[:offset]:
            requirements.append(Not(not_rank))

        return requirements

    @override
    def __str__(self) -> str:
        return f"{self._name}:{','.join([str(ref) for ref in self._refs])}"


# A metaclass to allow easy iteration over created courses
# https://stackoverflow.com/questions/32362148/typeerror-type-object-is-not-iterable-iterating-over-object-instances
# TODO: Technically, this might have a memory leak and I should learn what this
# actually is doing
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
        season: Offering | str,  # TODO: Deal with this
        requirements: Any = {},
        credits_repeatable_for: int | None = None,
    ):
        self._name: str = name
        self._id: Any = id
        self._requirements: Any = requirements
        self._credits: int = credits
        self._credits_repeatable_for: int | None = credits_repeatable_for
        self._season: Offering = Offering(season)
        self._refs: list[BoolRef] = []
        for _ in range(Course.semester_count + 1):  # +1 because allows a slot for transfer credits
            self._refs.append(RefManager.allocate(self))

        if self._id in Course.courses:
            raise KeyError(f"Key {self._id} already exists in course list")

        Course.courses[self._id] = self

    def get_id(self) -> Any:
        return self._id

    def get_name(self) -> str:
        return self._name

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

        formula = Or(self._refs[start_semester : end_semester + 1])
        if not isinstance(formula, BoolRef):
            raise TypeError("Expected id at semester to be a BoolRef")
        return formula

    def apply_cnf(self, solver: Optimize, sophomore: Rank, junior: Rank, senior: Rank, graduate: Rank, doctoral: Rank) -> None:
        solver.add(self._generate_seasonal_requirements())
        solver.add(self._generate_requisite_cnf(sophomore, junior, senior, graduate, doctoral))
        self._add_repeatable_requirement(solver)

    def _add_repeatable_requirement(self, solver: Optimize) -> None:
        if self._credits_repeatable_for is None:
            # If not stated otherwise, assume course can be taken at most once
            solver.add(sum(self._refs) <= 1)
        else:
            solver.add(sum([self._credits * ref for ref in self._refs]) <= self._credits_repeatable_for)

    def _generate_seasonal_requirements(self) -> Any:
        # Format is: ODD FALL, EVEN SPRING, EVEN FALL, ODD SPRING
        # Then gets rotates if needed
        offering_list: list[bool]

        match self._season:
            case Offering.FALL:
                offering_list = [True, False, True, False]
            case Offering.ODD_FALL:
                offering_list = [True, False, False, False]
            case Offering.EVEN_FALL:
                offering_list = [False, False, True, False]
            case Offering.SPRING:
                offering_list = [False, True, False, True]
            case Offering.ODD_SPRING:
                offering_list = [False, False, False, True]
            case Offering.EVEN_SPRING:
                offering_list = [False, True, False, False]
            case Offering.FALL_AND_SPRING | Offering.VARIABLE:
                offering_list = [True, True, True, True]

        # Going from starting fall to starting spring = 1 rotation
        # Going from odd starting year to even = 2 rotation
        if not starts_as_fall:
            offering_list = rotate(offering_list, 1)
        if start_year % 2 == 0:  # even starting year
            offering_list = rotate(offering_list, 2)

        not_offered_seasons: list[BoolRef] = []
        # Basically, require not taken when not offered
        for semester in range(1, Course.semester_count + 1):
            if not offering_list[(semester - 1) % 4]:
                not_offered_seasons.append(Not(self.at(semester)))

        return And(not_offered_seasons)

    def _generate_requisite_cnf(self, sophomore: Rank, junior: Rank, senior: Rank, graduate: Rank, doctoral: Rank) -> BoolRef:
        requirements: list[BoolRef] = []
        for semester in range(1, Course.semester_count + 1):
            not_taken: BoolRef = Not(self.at(semester))
            taken: BoolRef = self.at(semester)
            new_req: BoolRef | None = self.generate_requisites(self._requirements, semester, sophomore, junior, senior, graduate, doctoral)
            # Then, it condenses to not take or taken, which is a tautology, so unnecessary
            if new_req is None:
                continue
            requirements.append(Or(not_taken, And(taken, new_req)))
        return And(requirements)

    def generate_requisites(self, requirements: Any, semester: int, sophomore: Rank, junior: Rank, senior: Rank, graduate: Rank, doctoral: Rank) -> BoolRef | None:
        if len(requirements) == 0:
            return

        type = requirements.get("type")

        match type:
            case "PRE":
                course: Course = Course.by_id(requirements.get("value"))
                return course.at(start_semester=0, end_semester=semester - 1)
            case "CO":
                course: Course = Course.by_id(requirements.get("value"))
                return course.at(start_semester=0, end_semester=semester)
            case "RANK":
                # All requirements related to being a class rank
                value = requirements.get("value")
                if value == "sophomore":
                    return sophomore.at(semester)
                elif value == "junior":
                    return junior.at(semester)
                elif value == "senior":
                    return senior.at(semester)
                elif value == "graduate":
                    return graduate.at(semester)
                elif value == "doctoral":
                    return doctoral.at(semester)
                else:
                    raise ValueError(f"Invalid rank {value} detected while parsing requirements")
            case "NOT":
                req_to_negate = requirements.get("value")
                negated_req: Formula = Neg(self.generate_requisites(req_to_negate, semester, sophomore, junior, senior, graduate, doctoral))
                return negated_req
            case "MAJOR":
                raise NotImplementedError("Requirements based on major have not yet been implemented")
            case "AND":
                items: list[BoolRef] = []
                for item in requirements.get("items"):
                    items.append(self.generate_requisites(item, semester, sophomore, junior, senior, graduate, doctoral))
                return And(items)
            case "OR":
                items: list[BoolRef] = []
                for item in requirements.get("items"):
                    items.append(self.generate_requisites(item, semester, sophomore, junior, senior, graduate, doctoral))
                return Or(items)
            case _:
                raise ValueError(f"Cannot parse type '{type}' when parsing requirements")

    def __str__(self) -> str:
        return f"{self._id}:{self._name}:{','.join([str(ref) for ref in self._refs])}"


@typechecked
class CourseSATSolver:
    def __init__(
        self,
        semester_count: int,
        min_credit_per_semester: int,
        max_credits_per_semester: int,
        starts_as_fall: bool,
        start_year: int,
        first_semester_sophomore: int | None,
        first_semester_junior: int | None,
        first_semester_senior: int | None,
        first_semester_graduate: int | None,
        first_semester_doctoral: int | None,
        desired_course_ids: list[str],
    ):
        Course.semester_count = semester_count
        self.courses: list[Course] = load_courses(COURSES_FILE_NAME)
        self.min_credits_per_semester: int = min_credit_per_semester
        self.max_credits_per_semester: int = max_credits_per_semester
        self.starts_as_fall: bool = starts_as_fall
        self.start_year: int = start_year
        self.sophomore: Rank = Rank("sophomore", first_semester_sophomore)
        self.junior: Rank = Rank("junior", first_semester_junior)
        self.senior: Rank = Rank("senior", first_semester_senior)
        self.graduate: Rank = Rank("graduate", first_semester_graduate)
        self.doctoral: Rank = Rank("doctoral", first_semester_doctoral)
        self.desired_course_ids: list[str] = desired_course_ids
        self.plan: list[list[Course]] | None = None

        for course_id in transferred_course_ids:
            if not Course.by_id(course_id):
                raise Exception(f"Attempting to transfer an invalid course id '{course_id}'.")

    def setup(self) -> None:
        self.solver = Optimize()

        self._generate_bootstrap()

        for course in Course:
            print(f"Applying cnf for {course.get_name()}...")
            course.apply_cnf(self.solver, self.sophomore, self.junior, self.senior, self.graduate, self.doctoral)

        self._add_desired_courses()

        self._add_semester_credit_requirements()

    def _generate_bootstrap(self) -> None:
        self._generate_transfer_bootstrap()
        self._generate_rank_bootstrap()

    def _generate_transfer_bootstrap(self) -> None:
        transfer_courses: list[BoolRef] = []
        for course in Course:
            if course.get_id() in transferred_course_ids:
                transfer_courses.append(course.at(0))
            else:
                transfer_courses.append(Not(course.at(0)))
        self.solver.add(And(transfer_courses))

    def _generate_rank_bootstrap(self) -> None:
        rank_bootstrap: list[BoolRef] = []
        for rank in (self.sophomore, self.junior, self.senior, self.graduate, self.doctoral):
            rank_bootstrap.extend(rank.generate_bootstrap())
        self.solver.add(And(rank_bootstrap))

    def _add_desired_courses(self) -> None:
        desired_courses: list[Course] = [Course.by_id(id) for id in self.desired_course_ids]
        desired_refs: list[BoolRef] = [course.at(1, semester_count) for course in desired_courses]
        # NOTE: This *possibly* could be made into a soft constraint if we want
        # to return good courses even if invalid desire. Probably best to not
        # return anything if we cannot meet all desires though
        self.solver.add(And(desired_refs))

    def _add_semester_credit_requirements(self) -> None:
        for semester in range(1, semester_count + 1):
            refs: list[BoolRef] = [course.at(semester) for course in Course]
            weights: list[int] = [course.get_credits() for course in Course]

            # Upper bound
            self.solver.add(sum([weight * ref for weight, ref in zip(weights, refs)]) <= self.max_credits_per_semester)

            # Lower bound
            self.solver.add(sum([weight * ref for weight, ref in zip(weights, refs)]) >= self.min_credits_per_semester)

    def add_degree_reqs(self) -> None:
        self.solver.add(Or(Course.by_id("CS1800").get_refs()))
        self.solver.add(Or(Course.by_id("CS1520").get_refs()))
        self.solver.add(Or(Course.by_id("CS1410").get_refs()))

    # WARNING: Be careful, somethings this makes things take forever, right now
    # it seems to be behaving itself though
    def minimize(self) -> None:
        refs = []
        for course in Course.courses.values():
            refs.extend(course.get_refs())

        self.solver.minimize(sum(refs))

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

                reference_result: Any = RefManager.get(boolRef)
                if isinstance(reference_result, Course):
                    course: Course = reference_result
                    semester: int = course.get_refs().index(boolRef)

                    if model[boolRef]:
                        self.plan[semester].append(course)

        else:
            print("UNSAT")

    def display(self) -> None:
        if self.plan is None:
            raise ValueError("CourseSATSolver needs to be solver before a plan can be displayed")

        for i, semester in enumerate(self.plan):
            semester_name: str
            if i == 0:
                semester_name = "Transferred"
            else:
                semester_name = self._get_semester_name(i)
            print(f"Semester {i}: {semester_name}")
            for course in sorted(semester, key=lambda course: course.get_id()):
                print(f"\t{course}")

    def _get_semester_name(self, semester: int) -> str:
        season: str
        year: int
        if self.starts_as_fall:
            season = "Fall" if semester % 2 == 1 else "Spring"
            year = start_year + (semester // 2)
        else:
            season = "Spring" if semester % 2 == 1 else "Fall"
            year = start_year + ((semester - 1) // 2)
        return f"{season} {year}"


def load_courses(file_name: str) -> list[Course]:
    with open(file_name, "r") as file:
        raw_courses = json.load(file)["courses"]

    return [Course(**course) for course in raw_courses]


if __name__ == "__main__":
    c: CourseSATSolver = CourseSATSolver(
        semester_count=semester_count,
        min_credit_per_semester=min_credit_per_semester,
        max_credits_per_semester=max_credits_per_semester,
        first_semester_sophomore=first_semester_sophomore,
        first_semester_junior=first_semester_junior,
        first_semester_senior=first_semester_senior,
        first_semester_graduate=first_semester_graduate,
        first_semester_doctoral=first_semester_doctoral,
        starts_as_fall=starts_as_fall,
        start_year=start_year,
        desired_course_ids=desired_course_ids,
    )

    c.setup()
    c.add_degree_reqs()
    c.minimize()
    c.solve()
    c.display()
