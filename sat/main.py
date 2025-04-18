from enum import StrEnum
import json
from typing import Any, Generator, TypeVar, override

from typeguard import typechecked
from z3.z3 import And, Bool, BoolRef, BoolVal, ModelRef, Not, Optimize, Or, sat  # type: ignore[import-untyped]

from config import COURSES_FILE_NAME, DEGREES_FILE_NAME

from degree_requirement_manager import DegreeRequirementManager

##########################
### START CONFIG VARIABLES
##########################
# These will all be taken as input from the user
semester_count = 4  # Number of semester to calculate for
min_credit_per_semester = 3  # Minimum credits (inclusive)
max_credits_per_semester = 16  # Maximum credits (inclusive)
starts_as_fall = True
start_year = 2025
transferred_course_ids: list[str] = []  # ["CS1410", "CS1510"]
desired_course_ids: list[tuple[str] | tuple[str, int]] = [
    ("CS3430/5430", 4),
    # ("CS1160",),
]
undesired_course_ids: list[tuple[str] | tuple[str, int]] = [
    ("CS4410/5410",),
]
desired_degree_ids: list[str] = ["CS:BA"]
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


# TODO: Implement degrees
@typechecked
class Degree:
    degrees: dict[str, "Degree"] = {}

    @classmethod
    def by_id(cls, id: Any) -> "Degree":
        if id not in cls.degrees:
            raise IndexError(f"Unable to find id '{id}' in courses")
        return cls.degrees[id]

    def __init__(
        self,
        id: Any,
        name: str,
        requirements: dict[Any, Any] = {},
    ):
        self._id: Any = id
        self._name: str = name
        self._ref = RefManager.allocate(self)
        self._requirements: DegreeRequirementManager = DegreeRequirementManager(requirements)

        if self._id in Degree.degrees:
            raise KeyError(f"Key {self._id} already exists in degree list")

        self.degrees[self._id] = self

    @classmethod
    def setup(
        cls,
        sophomore: "Rank",
        junior: "Rank",
        senior: "Rank",
        graduate: "Rank",
        doctoral: "Rank",
    ) -> None:
        for degree in cls.degrees.values():
            degree.get_requirements().setup(Course, Degree, sophomore, junior, senior, graduate, doctoral)
            print("Printing degree requirement classes:")
            for course in degree.get_requirements().get_courses():
                print(f"\t{course._name}")

    def get_requirements(self) -> DegreeRequirementManager:
        return self._requirements

    def generate_cnf(self) -> BoolRef:
        return self._requirements.generate()

    @override
    def __str__(self) -> str:
        return f"{self._id}:{self._name}:{str(self._ref)}"


# TODO: I should probably have a RankManager, then it has references to
# junior, senior, etc...
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

    def at(self, start_semester: int | None = None, end_semester: int | None = None) -> BoolRef:
        # TODO: This way of doing things is not very clear
        if start_semester is None and end_semester is None:
            start_semester = 0
            end_semester = Course.semester_count

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

        course: Course

        match type:
            case "PRE":
                course = Course.by_id(requirements.get("value"))
                return course.at(start_semester=0, end_semester=semester - 1)
            case "CO":
                course = Course.by_id(requirements.get("value"))
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
                negated_req: BoolRef = Not(self.generate_requisites(req_to_negate, semester, sophomore, junior, senior, graduate, doctoral))
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
        desired_course_ids: list[tuple[str] | tuple[str, int]],
        undesired_course_ids: list[tuple[str] | tuple[str, int]],
        desired_degree_ids: list[str],
    ):
        Course.semester_count = semester_count
        self.courses: list[Course] = load_courses(COURSES_FILE_NAME)
        self.degrees: list[Degree] = load_degrees(DEGREES_FILE_NAME)
        self.min_credits_per_semester: int = min_credit_per_semester
        self.max_credits_per_semester: int = max_credits_per_semester
        self.starts_as_fall: bool = starts_as_fall
        self.start_year: int = start_year
        self.sophomore: Rank = Rank("sophomore", first_semester_sophomore)
        self.junior: Rank = Rank("junior", first_semester_junior)
        self.senior: Rank = Rank("senior", first_semester_senior)
        self.graduate: Rank = Rank("graduate", first_semester_graduate)
        self.doctoral: Rank = Rank("doctoral", first_semester_doctoral)
        self.desired_course_ids: list[tuple[str] | tuple[str, int]] = desired_course_ids
        self.undesired_course_ids: list[tuple[str] | tuple[str, int]] = undesired_course_ids
        self.desired_degree_ids: list[str] = desired_degree_ids
        self.plan: list[list[Course]] | None = None

        for degree in self.degrees:
            degree.setup(
                self.sophomore,
                self.junior,
                self.senior,
                self.graduate,
                self.doctoral,
            )

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
        self._add_undesired_courses()

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
        desired_refs = []
        for pair in self.desired_course_ids:
            id: str = pair[0]
            course = Course.by_id(id)
            count: int | None = pair[1] if len(pair) > 1 else None
            if count is None:
                desired_refs.append(course.at(1, semester_count))
            else:
                desired_refs.append(course.at(count, count))

        # NOTE: This *possibly* could be made into a soft constraint if we want
        # to return good courses even if invalid desire. Probably best to not
        # return anything if we cannot meet all desires though
        self.solver.add(And(desired_refs))

    # TODO: Make this work
    def _add_undesired_courses(self) -> None:
        undesired_refs = []
        for pair in self.undesired_course_ids:
            id: str = pair[0]
            course = Course.by_id(id)
            count: int | None = pair[1] if len(pair) > 1 else None
            if count is None:
                undesired_refs.append(And([Not(course.at(i, i)) for i in range(1, semester_count + 1)]))
            else:
                undesired_refs.append(Not(course.at(count, count)))

        # NOTE: This *possibly* could be made into a soft constraint if we want
        # to return good courses even if invalid desire. Probably best to not
        # return anything if we cannot meet all desires though
        self.solver.add(And(undesired_refs))

    def _add_semester_credit_requirements(self) -> None:
        for semester in range(1, semester_count + 1):
            refs: list[BoolRef] = [course.at(semester) for course in Course]
            weights: list[int] = [course.get_credits() for course in Course]

            # Upper bound
            self.solver.add(sum([weight * ref for weight, ref in zip(weights, refs)]) <= self.max_credits_per_semester)

            # Lower bound
            self.solver.add(sum([weight * ref for weight, ref in zip(weights, refs)]) >= self.min_credits_per_semester)

    # TODO: Implementation might be weird with courses requiring you have a specific
    # major, when not all majors have references.
    def add_degree_reqs(self) -> None:
        for degree_id in self.desired_degree_ids:
            self.solver.add(Degree.by_id(degree_id).generate_cnf())

    # WARNING: Be careful, somethings this makes things take forever, right now
    # it seems to be behaving itself though
    def minimize(self) -> None:
        refs = []
        for course in Course.courses.values():
            refs.extend(course.get_refs())

        self.solver.minimize(sum(refs))

    # TODO: Could implement a pseudo-minimization by after we solve it, going through
    # and setting each variable to false then seeing if you are still sat.
    # Somehow  you have to make sure it doesn't just as a ton of other classes
    # though... not sure how to do that part
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


def load_degrees(file_name: str) -> list[Degree]:
    with open(file_name, "r") as file:
        raw_degrees = json.load(file)["degrees"]

    degrees = [Degree(**degree) for degree in raw_degrees]

    for degree in degrees:
        print(degree)

    return degrees


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
        undesired_course_ids=undesired_course_ids,
        desired_degree_ids=desired_degree_ids,
    )

    c.setup()
    c.add_degree_reqs()
    c.minimize()
    c.solve()
    c.display()
