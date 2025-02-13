import json
from enum import StrEnum
from typing import Any, override

from pysat.solvers import Solver
from pysat.formula import And, Or, Neg, Atom, Formula
from typeguard import typechecked

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


class ExtSolver(Solver):
    def add_atleast(self, lits, k, weights=[], no_return=True):
        negative_lits: list[int] = [-lit for lit in lits]
        altered_k = sum(weights) - k
        return self.add_atmost(lits=negative_lits, weights=weights, k=altered_k)


class Offering(StrEnum):
    FALL = "FALL"
    SPRING = "SPRING"
    FALL_AND_SPRING = "FALL_AND_SPRING"
    VARIES = "VARIES"
    EVEN_FALL = "EVEN_FALL"
    ODD_FALL = "ODD_FALL"
    EVEN_SPRING = "EVEN_SPRING"
    ODD_SPRING = "ODD_SPRING"


def rotate(lst, n):
    return lst[-n:] + lst[:-n]


@typechecked
class IndexManager:
    count = 0
    store = {}

    @classmethod
    def allocate(cls, value: Any, n: int = 1) -> Atom:
        # Update the count
        IndexManager.count += 1
        # Add new item to the store
        IndexManager.store[Atom(IndexManager.count)] = value
        # Return items id
        return Atom(IndexManager.count)

    @classmethod
    def get(cls, id: Atom) -> Any:
        if id not in IndexManager.store:
            raise KeyError(f"Cannot find id '{id}' in store")
        return IndexManager.store[id]

    @classmethod
    def find(cls, value: Any, default_return: Any = -1) -> Any | None:
        for k, v in IndexManager.store.items():
            if v == value:
                return k
        return default_return


@typechecked
class Rank:
    # first_semester_with_rank of None is intepreted as you never become the rank
    # first_semester_with_rank of 0 is intepreted as you start with the rank
    def __init__(self, name: str, first_semester_with_rank: int | None):
        self.name: str = name
        self.first_semester_with_rank: int | None = first_semester_with_rank
        self.indices: list[Atom] = []
        for _ in range(semester_count):
            self.indices.append(IndexManager.allocate(self))

        if (first_semester_with_rank is not None) and (first_semester_with_rank < 1 or first_semester_with_rank > semester_count):
            raise ValueError(f"Cannot start semester with rank {name} cannot be before first semester or after last semester. Set as None if never reached, and 0 is instantly reached.")

    def at(self, semester: int) -> Any:
        if semester < 1 or semester > semester_count:
            raise ValueError(f"Cannot check for rank {self.name} during semester below 1 or above {semester_count}")
        return self.indices[semester - 1]

    def generate_bootstrap(self) -> list[list[int]]:
        requirements: list[list[int]] = []

        if self.first_semester_with_rank is None:
            offset = semester_count
        else:
            offset = self.first_semester_with_rank - 1

        for not_rank in self.indices[:offset]:
            if not isinstance(not_rank.object, int):
                raise TypeError(f"Index should have been of type int, instead found '{not_rank.object}'")
            requirements.append([-1 * not_rank.object])
        for rank in self.indices[offset:]:
            if not isinstance(rank.object, int):
                raise TypeError(f"Index should have been of type int, instead found '{rank.object}'")
            requirements.append([rank.object])

        return requirements

    @override
    def __str__(self) -> str:
        return f"{self.name}:{','.join([str(idx) for idx in self.indices])}"


@typechecked
class Course:
    courses: dict[Any, "Course"] = {}
    semester_count: int

    @classmethod
    def by_id(cls, id) -> "Course":
        return cls.courses[id]

    # id is received from courses and is ultimately returned
    # indices tracks location in boolean expression/which semester a class is taken
    def __init__(
        self,
        name: str,
        id: Any,
        credits: int,
        requirements: Any,
        season: Offering | str,
        credits_repeatable_for: int | None = None,
    ):
        self.name: str = name
        self.id: Any = id
        self.requirements: Any = requirements
        self.credits: int = credits
        self.credits_repeatable_for: int | None = credits_repeatable_for
        self.season: Offering = Offering(season)
        self.indices: list[Atom] = []
        for _ in range(Course.semester_count + 1):  # +1 because allows a slot for transfer credits
            self.indices.append(IndexManager.allocate(self))

        if self.id in Course.courses:
            raise KeyError(f"Key {self.id} already exists in course list")

        Course.courses[self.id] = self

    def get_indices(self) -> list[Atom]:
        return self.indices

    def get_credits(self) -> int:
        return self.credits

    def at(self, start_semester: int, end_semester: int | None = None) -> Formula:
        if start_semester < 0 or start_semester > Course.semester_count:
            raise ValueError(f"Cannot check for rank {self.name} during semester starting below 0 (transfers) or above {Course.semester_count}")

        if end_semester is None:
            return self.indices[start_semester]

        if end_semester < 0 or end_semester > Course.semester_count:
            raise ValueError(f"Cannot check for rank {self.name} during semester ending below 0 (transfers) or above {Course.semester_count}")
        if end_semester < start_semester:
            raise ValueError(f"Cannot check for rank {self.name} with end semester before start semester")

        return Or(*self.indices[start_semester : end_semester + 1])

    def apply_cnf(self, solver: Solver, junior: Rank, senior: Rank) -> None:
        solver.append_formula([f for f in self.generate_requisite_cnf(junior, senior)])
        solver.append_formula([f for f in self.generate_seasonal_requirements()])
        self.add_repeatable_requirement(solver)

    def add_repeatable_requirement(self, solver: Solver) -> None:
        lits: list[int] = [a.object for a in self.indices]
        weight: list[int] = [self.credits for _ in range(len(self.indices))]
        if self.credits_repeatable_for is None:
            # None means class can be taken only once, so no weighting necessary
            solver.add_atmost(lits, 1)
        else:
            solver.add_atmost(lits, weights=weight, k=self.credits_repeatable_for)

    def generate_requisite_cnf(self, junior: Rank, senior: Rank) -> Formula:
        requirements: list[Formula] = []
        for semester in range(1, Course.semester_count + 1):
            not_taken: Formula = Neg(self.at(semester))
            taken: Formula = self.at(semester)
            new_req: Formula | None = self.generate_requisites(self.requirements, semester, junior, senior)
            if new_req is None:
                continue
            requirements.append(Or(not_taken, And(taken, new_req)))
        return And(*requirements)

    def generate_seasonal_requirements(self) -> Formula:
        # Format is: ODD FALL, EVEN SPRING, EVEN FALL, ODD SPRING
        # Then gets rotates if needed
        offering_list: list[bool]

        match self.season:
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
            case Offering.FALL_AND_SPRING | Offering.VARIES:
                offering_list = [True, True, True, True]

        # Going from starting fall to starting spring = 1 rotation
        # Going from odd starting year to even = 2 rotation
        if not starts_as_fall:
            offering_list = rotate(offering_list, 1)
        if start_year % 2 == 0:  # even starting year
            offering_list = rotate(offering_list, 2)

        formula: list[Formula] = []
        # Basically, require not taken when not offered
        for semester in range(1, Course.semester_count + 1):
            if not offering_list[(semester - 1) % 4]:
                formula.append(Neg(self.at(semester)))

        return And(*formula)

    def generate_requisites(self, requirements: Any, semester: int, junior: Rank, senior: Rank) -> Formula | None:
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
                # All requirements related to being a junior or senior
                value = requirements.get("value")
                if value == "JR":
                    return junior.at(semester)
                elif value == "SR":
                    return senior.at(semester)
                else:
                    raise ValueError(f"Invalid rank {value} detected while parsing requirements")
            case "NOT":
                req_to_negate = requirements.get("value")
                negated_req: Formula = Neg(self.generate_requisites(req_to_negate, semester, junior, senior))
                return negated_req
            case "MAJOR":
                raise NotImplementedError("Requirements based on major have not yet been implemented")
            case "AND":
                items: list[Formula] = []
                for item in requirements.get("items"):
                    items.append(self.generate_requisites(item, semester, junior, senior))
                return And(*items)
            case "OR":
                items: list[Formula] = []
                for item in requirements.get("items"):
                    items.append(self.generate_requisites(item, semester, junior, senior))
                return Or(*items)
            case _:
                raise ValueError(f"Cannot parse type '{type}' when parsing requirements")

    def __str__(self):
        return f"{self.id}:{self.name}:{','.join([str(x) for x in self.indices])}"


@typechecked
class CourseSATSolver:
    def __init__(
        self,
        semester_count: int,
        min_credit_per_semester: int,
        max_credits_per_semester: int,
        starts_as_fall: bool,
        start_year: int,
        transferred_course_ids: list[int],
        first_semester_junior: int | None,
        first_semester_senior: int | None,
    ):
        Course.semester_count = semester_count
        self.courses: list[Course] = load_courses(COURSES_FILE_NAME)
        self.min_credits_per_semester: int = min_credit_per_semester
        self.max_credits_per_semester: int = max_credits_per_semester
        self.starts_as_fall: bool = starts_as_fall
        self.start_year: int = start_year
        self.transferred_course_ids: list[int] = transferred_course_ids
        self.junior: Rank = Rank("junior", first_semester_junior)
        self.senior: Rank = Rank("senior", first_semester_senior)
        self.plans: list[list[list[Course]]] | None = None

        for course_id in transferred_course_ids:
            if not Course.by_id(course_id):
                raise Exception(f"Attempting to transfer an invalid course id '{course_id}'.")

    def setup(self) -> None:
        self.solver = ExtSolver(name="Cadical195", bootstrap_with=self._generate_bootstrap())
        self.solver.activate_atmost()

        self._add_semester_credit_requirements()

        for course in Course.courses.values():
            course.apply_cnf(self.solver, self.junior, self.senior)

    def solve(self) -> None:
        self.possible_plans: list[list[list[Course]]] = []

        for k, v in IndexManager.store.items():
            print(f"{k}: {v}")

        if self.solver.solve():
            print("SAT")
            # Loop through all solutions
            for model in self.solver.enum_models():
                # print("\nNext Model")
                semesters: list[list[Course]] = [[] for _ in range(semester_count)]
                # This well you what each id actually means, that is
                # id 24 might represent 12 & ( 3 | 4)
                idp = Formula.export_vpool().id2obj
                # Look through every variable in the model
                for k in model:
                    value = idp[abs(k)]
                    # print(value, type(value))
                    # We only care about displaying Atoms (which represent classes), not constraints
                    # print(k, value)
                    if not isinstance(value, Atom):
                        break
                    if k > 0:  # less than 0 means *not* taken class
                        # semester = (abs(k) - 1) // Course.course_count
                        course = IndexManager.get(value)
                        if not isinstance(course, Course):
                            continue
                        idx = course.get_indices().index(value)
                        semesters[idx - 1].append(course)

                self.possible_plans.append(semesters)
        else:
            print("UNSAT")

    def display(self) -> None:
        for i, plan in enumerate(self.possible_plans):
            print(f"Plan {i + 1}")
            for semester, semester_courses in enumerate(plan):
                print(f"\t{self.get_semester_name(semester + 1)}")
                for course in semester_courses:
                    print(f"\t\t{course.name}")
            print()

    def _generate_bootstrap(self) -> list[list[int]]:
        bootstrap: list[list[int]] = []
        bootstrap.extend(self._generate_transferred_bootstrap())
        bootstrap.extend(self.junior.generate_bootstrap())
        bootstrap.extend(self.senior.generate_bootstrap())
        return bootstrap

    def _generate_transferred_bootstrap(self) -> list[list[int]]:
        bootstrap: list[list[int]] = []

        for course in Course.courses.values():
            transfer_index = course.at(0)
            if course.id in self.transferred_course_ids:
                # The course has been taken
                bootstrap.append([transfer_index.object])
            else:
                # The course has NOT been taken
                bootstrap.append([-1 * transfer_index.object])

        return bootstrap

    def _add_semester_credit_requirements(self) -> None:
        for semester in range(1, semester_count + 1):
            course_lits: list[int] = [course.at(semester).object for course in Course.courses.values()]
            weights: list[int] = [course.get_credits() for course in Course.courses.values()]

            # Upper bound
            self.solver.add_atmost(lits=course_lits, weights=weights, k=self.max_credits_per_semester)

            # Lower bound
            self.solver.add_atleast(lits=course_lits, weights=weights, k=self.min_credits_per_semester)

    def get_semester_name(self, semester: int) -> str:
        season: str
        year: int
        if self.starts_as_fall:
            season = "Fall" if semester % 2 == 1 else "Spring"
            year = start_year + (semester // 2)
        else:
            season = "Spring" if semester % 2 == 1 else "Fall"
            year = start_year + ((semester - 1) // 2)
        return f"{season} {year}"


def load_courses(file_name) -> list[Course]:
    with open(file_name, "r") as file:
        raw_courses = json.load(file)["courses"]

    return [Course(**course) for course in raw_courses]


if __name__ == "__main__":
    c: CourseSATSolver = CourseSATSolver(
        semester_count,
        min_credit_per_semester,
        max_credits_per_semester,
        starts_as_fall,
        start_year,
        transferred_course_ids,
        first_semester_junior,
        first_semester_senior,
    )

    c.setup()
    c.solve()
    c.display()
