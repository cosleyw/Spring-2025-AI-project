from collections import Counter
from enum import StrEnum
import json
from typing import Any, Generator, TypeVar, override
import os

from typeguard import typechecked
from z3 import Implies
from z3.z3 import And, ArithRef, Bool, BoolRef, BoolVal, Int, IntNumRef, ModelRef, Not, Optimize, Or, sat  # type: ignore[import-untyped]

from config import COURSES_FILE_NAME, DATA_DIR, DEGREES_FILE_NAME

from degree_requirement_manager import DegreeRequirementManager

import logging

# Alternated format for date - datefmt='%Y-%m-%d:%H:%M:%S',
logging.basicConfig(
    filename="log.out",
    level=logging.DEBUG,
    format="%(asctime)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

# Log to both terminal and stdout (technically might be stderr)
logging.getLogger().addHandler(logging.StreamHandler())


@typechecked
class Offering(StrEnum):
    FALL_SPRING_SUMMER = "FALL, SPRING, SUMMER"
    SPRING = "SPRING"
    FALL = "FALL"
    FALL_AND_SPRING = "FALL AND SPRING"
    SUMMER = "SUMMER"
    VARIABLE = "VARIABLE"
    ODD_SPRINGS = "ODD SPRINGS"
    ODD_FALLS = "ODD FALLS"
    EVEN_SPRINGS = "EVEN SPRINGS"
    EVEN_FALLS = "EVEN FALLS"
    ODD_SUMMERS = "ODD SUMMERS"
    SPRING_AND_SUMMER = "SPRING AND SUMMER"
    FALL_OR_SPRING = "FALL OR SPRING"
    EVEN_SUMMERS = "EVEN SUMMERS"
    FALL_AND_VARIABLE_SPRINGS = "FALL AND VARIABLE SPRINGS"
    SPRING_AND_EVEN_FALLS = "SPRING AND EVEN FALLS"
    SPRING_AND_VARIABLE_FALLS = "SPRING AND VARIABLE FALLS"


T = TypeVar("T")


@typechecked
def rotate(lst: list[T], n: int) -> list[T]:
    return lst[-n:] + lst[:-n]


@typechecked
class RefManager:
    def __init__(self):
        self.count: int = 0
        self.store: dict[BoolRef, Any] = {}

    def allocate_int(self, value: Any) -> ArithRef:
        self.count += 1
        return Int(self.count)

    def allocate(self, value: Any) -> BoolRef:
        # Update the count
        self.count += 1
        # Add new item to the store
        allocated_value: BoolRef = Bool(self.count)
        self.store[allocated_value] = value
        # Return items id
        return allocated_value

    def get(self, id: BoolRef) -> Any:
        if id not in self.store:
            raise KeyError(f"Cannot find id '{id}' in store")
        return self.store[id]

    # def find(self, value: Any, default_return: Any = -1) -> Any | None:
    #    for k, v in self.store.items():
    #        if v == value:
    #            return k
    #    return default_return


@typechecked
class DegreeManager:
    def __init__(self):
        self.degrees: dict[str, "Degree"] = {}

    def setup(
        self,
        sophomore: "Rank",
        junior: "Rank",
        senior: "Rank",
    ) -> None:
        for degree in self:
            degree.get_requirements().setup()
            logging.debug("Printing degree requirement classes:")
            for course in degree.get_requirements().get_courses():
                logging.debug(f"\t{course._name}")

    def add_degree(self, degree: "Degree"):
        if degree.get_id() in self.degrees:
            raise KeyError(f"Key {degree.get_id()} already exists in degree list")

        logging.debug(f"Loading degree {degree.get_id()}")
        self.degrees[degree.get_id()] = degree

    def by_id(self, id: Any) -> "Degree":
        if id not in self.degrees:
            raise IndexError(f"Unable to find id '{id}' in degrees")
        return self.degrees[id]

    def __iter__(self) -> Generator["Degree", Any, None]:
        yield from self.degrees.values()


@typechecked
class Degree:
    def __init__(
        self,
        id: Any,
        name: str,
        course_manager: "CourseManager",
        ref_manager: "RefManager",
        requirements: dict[Any, Any] = {},
    ):
        self._id: Any = id
        self._name: str = name
        self._ref = ref_manager.allocate(self)
        self._requirements: DegreeRequirementManager = DegreeRequirementManager(course_manager, id, requirements)

    def get_requirements(self) -> DegreeRequirementManager:
        return self._requirements

    def generate_cnf(self) -> BoolRef:
        return self._requirements.generate()

    def get_id(self):
        return self._id

    @override
    def __str__(self) -> str:
        return f"{self._id}:{self._name}:{str(self._ref)}"


# TODO: I should probably have a RankManager, then it has references to
# junior, senior, etc...
@typechecked
class Rank:
    # first_semester_with_rank of None is intepreted as you never become the rank
    # first_semester_with_rank of 0 is intepreted as you start with the rank
    def __init__(self, name: str, first_semester_with_rank: int | None, semester_count: int, ref_manager: "RefManager"):
        self._name: str = name
        self._first_semester_with_rank: int | None = first_semester_with_rank
        self._refs: list[BoolRef] = []
        self._semester_count: int = semester_count
        for _ in range(semester_count):
            self._refs.append(ref_manager.allocate(self))

        if (first_semester_with_rank is not None) and (first_semester_with_rank < 1 or first_semester_with_rank > semester_count):
            raise ValueError(f"Cannot start semester with rank {name} cannot be before first semester or after last semester. Set as None if never reached, and 0 is instantly reached.")

    def at(self, semester: int) -> BoolRef:
        if semester < 1 or semester > self._semester_count:
            raise ValueError(f"Cannot check for rank {self._name} during semester below 1 or above {self._semester_count}")
        return self._refs[semester - 1]

    def generate_bootstrap(self) -> list[BoolRef]:
        requirements: list[BoolRef] = []

        if self._first_semester_with_rank is None:
            offset = self._semester_count
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


@typechecked
class CourseManager:
    def __init__(self, semester_count: int):
        self._semester_count: int = semester_count
        self._courses: dict[Any, "Course"] = {}

    def add_course(self, course: "Course") -> None:
        if course.get_id() in self._courses:
            raise KeyError(f"Key {course.get_id()} already exists in course list")

        logging.debug(f"Loading course {course.get_id()}")
        self._courses[course.get_id()] = course

    def __iter__(self) -> Generator["Course", Any, None]:
        yield from self._courses.values()

    def by_id(self, id: Any) -> "Course":
        if id not in self._courses:
            raise IndexError(f"Unable to find id '{id}' in courses")
        return self._courses[id]

    def get_semester_count(self) -> int:
        return self._semester_count


@typechecked
class Course:
    # id is received from courses and is ultimately returned
    # refs tracks location in boolean expression/which semester a class is taken
    def __init__(
        self,
        name: str,
        id: Any,
        hours: list[int],
        semester: Offering | str,
        course_manager: "CourseManager",
        ref_manager: "RefManager",
        starts_as_fall: bool,
        start_year: int,
        dept: str,
        number: str,
        prereq: Any = {},
        coreq: Any = {},
        preorco: Any = {},
        credits_repeatable_for: int | None = None,
        desc: str | None = None,
    ):
        self._name: str = name
        self._id: Any = id
        self._requirements: Any = {
            "prereq": prereq,
            "coreq": coreq,
            "preorco": preorco,
        }
        self._dept: str = dept
        self._number: str = number
        # TODO: This is not the best solution, but works for now
        self._min_credits = hours[0]
        self._max_credits = hours[-1]

        if self._min_credits == self._max_credits:
            self._credits = hours[0]
        else:
            self._credits = ref_manager.allocate_int(self)

        self._credits_repeatable_for: int | None = credits_repeatable_for
        self._starts_as_fall = starts_as_fall
        self._start_year = start_year
        self._season: Offering = Offering(semester.upper())
        self._refs: list[BoolRef] = []
        self._taken_for_specific_rg: dict[str, list[BoolRef]] = {}
        self._course_manager: CourseManager = course_manager
        self._ref_manager: RefManager = ref_manager
        for _ in range(self._course_manager.get_semester_count() + 1):  # +1 because allows a slot for transfer credits
            self._refs.append(self._ref_manager.allocate(self))

    def is_variable_credits(self):
        return self._min_credits != self._max_credits

    def get_id(self) -> Any:
        return self._id

    def get_name(self) -> str:
        return self._name

    def get_refs(self) -> list[BoolRef]:
        return self._refs

    def get_credits(self) -> int | ArithRef:
        return self._credits

    def add_as_degree_req(self, degree_id: str) -> BoolRef:
        ref = self._ref_manager.allocate(None)
        if degree_id not in self._taken_for_specific_rg:
            self._taken_for_specific_rg[degree_id] = []
        self._taken_for_specific_rg[degree_id].append(ref)
        return ref

    def get_taken_as_degree_req(self, degree_id: str) -> list[BoolRef]:
        return self._taken_for_specific_rg[degree_id]

    def generate_taken_requirement_cnf(self) -> BoolRef:
        requirements: list[BoolRef] = []

        # If taken for credit, it has to be taken!
        for taken_for_degree in self._taken_for_specific_rg.values():
            for taken_for_specific_rg in taken_for_degree:
                requirements.append(Implies(taken_for_specific_rg, Or(self.at())))

        # Cannot take for credit multiple places for a single degree
        # but can take across multiple degrees
        for taken_for_degree in self._taken_for_specific_rg.values():
            requirements.append(sum(taken_for_degree) <= 1)

        return And(requirements)

    def at(self, start_semester: int | None = None, end_semester: int | None = None) -> BoolRef:
        # TODO: This way of doing things is not very clear. Can probably be
        # largely re-written after more tessting is implemented.
        total_semester_count: int = self._course_manager.get_semester_count()

        if start_semester is None and end_semester is None:
            start_semester = 0
            end_semester = total_semester_count

        if start_semester < 0 or start_semester > self._course_manager.get_semester_count():
            raise ValueError(f"Cannot check for rank {self._name} during semester starting below 0 (transfers) or above {total_semester_count}: received {start_semester}")

        if end_semester is None:
            return self._refs[start_semester]

        if end_semester < 0 or end_semester > total_semester_count:
            raise ValueError(f"Cannot check for rank {self._name} during semester ending below 0 (transfers) or above {total_semester_count}")
        if end_semester < start_semester:
            raise ValueError(f"Cannot check for rank {self._name} with end semester before start semester")

        formula = Or(self._refs[start_semester : end_semester + 1])
        if not isinstance(formula, BoolRef):
            raise TypeError("Expected id at semester to be a BoolRef")
        return formula

    def apply_cnf(self, solver: Optimize, sophomore: Rank, junior: Rank, senior: Rank) -> None:
        self._add_variable_credit_requirement(solver)
        solver.add(self._generate_seasonal_requirements())
        solver.add(self._generate_requisite_cnf(sophomore, junior, senior))
        self._add_repeatable_requirement(solver)

    def _add_variable_credit_requirement(self, solver: Optimize) -> None:
        # if set number of credits, nothing needs to be added
        if self.is_variable_credits():
            solver.add(And(self._max_credits >= self.get_credits(), self.get_credits() >= self._min_credits))

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
            case Offering.ODD_FALLS:
                offering_list = [True, False, False, False]
            case Offering.SPRING_AND_EVEN_FALLS:
                offering_list = [False, True, True, True]
            case Offering.EVEN_FALLS:
                offering_list = [False, False, True, False]
            case Offering.SPRING | Offering.SPRING_AND_SUMMER:
                offering_list = [False, True, False, True]
            case Offering.ODD_SPRINGS:
                offering_list = [False, False, False, True]
            case Offering.EVEN_SPRINGS:
                offering_list = [False, True, False, False]
            case Offering.FALL_SPRING_SUMMER | Offering.FALL_AND_SPRING | Offering.VARIABLE | Offering.FALL_OR_SPRING | Offering.FALL_AND_VARIABLE_SPRINGS | Offering.SPRING_AND_VARIABLE_FALLS:
                offering_list = [True, True, True, True]
            case Offering.SUMMER | Offering.EVEN_SUMMERS | Offering.ODD_SUMMERS:
                offering_list = [False, False, False, False]
            case _:
                raise NotImplementedError(f"Not yet implemented offering for {self._season}...")

        # Going from starting fall to starting spring = 1 rotation
        # Going from odd starting year to even = 2 rotation
        if not self._starts_as_fall:
            offering_list = rotate(offering_list, 1)
        if self._start_year % 2 == 0:  # even starting year
            offering_list = rotate(offering_list, 2)

        not_offered_seasons: list[BoolRef] = []
        # Basically, require not taken when not offered
        for semester in range(1, self._course_manager.get_semester_count() + 1):
            if not offering_list[(semester - 1) % 4]:
                not_offered_seasons.append(Not(self.at(semester)))

        return And(not_offered_seasons)

    def _generate_requisite_cnf(self, sophomore: Rank, junior: Rank, senior: Rank) -> BoolRef:
        requirements: list[BoolRef] = []
        for semester in range(1, self._course_manager.get_semester_count() + 1):
            not_taken: BoolRef = Not(self.at(semester))
            taken: BoolRef = self.at(semester)
            new_req: BoolRef | None = self.generate_requisites(self._requirements, semester, sophomore, junior, senior)
            # Then, it condenses to not take or taken, which is a tautology, so unnecessary
            if new_req is None:
                continue
            requirements.append(Or(not_taken, And(taken, new_req)))
        return And(requirements)

    def generate_requisites(self, requirements: Any, semester: int, sophomore: Rank, junior: Rank, senior: Rank) -> BoolRef | None:
        def generate_requisites_helper(requirements: Any, mode: str) -> BoolRef | None:
            # logging.debug(f"{requirements}, {mode}")
            # if len(requirements) == 0:
            #    return

            type = requirements.get("type")

            course: Course

            match type:
                case "course":
                    course_id = requirements.get("dept") + " " + requirements.get("number")
                    try:
                        course = self._course_manager.by_id(course_id)
                    except Exception as e:
                        logging.warning(e)
                        return BoolVal(False)
                    if mode == "prereq":
                        start_semester = 0
                        end_semester = semester - 1
                    elif mode == "preorco":
                        start_semester = 0
                        end_semester = semester
                    elif mode == "coreq":
                        start_semester = semester
                        end_semester = semester
                    else:
                        raise TypeError(f"Expected mode to be prereq, preorco, or coreq, instead received {mode} for {requirements}")
                    return course.at(start_semester, end_semester)
                case "standing":
                    # All requirements related to being a class rank
                    standing = requirements.get("value")
                    if standing == "sophomore":
                        return sophomore.at(semester)
                    elif standing == "junior":
                        return junior.at(semester)
                    elif standing == "senior":
                        return senior.at(semester)
                    elif standing == "graduate":
                        return BoolVal(False)
                    else:
                        raise ValueError(f"Invalid rank '{standing}' detected while parsing requirements")
                case "all":
                    reqs: list[BoolRef] = []
                    for req in requirements.get("req"):
                        reqs.append(generate_requisites_helper(req, mode))
                    return And(reqs)
                case "some":
                    reqs: list[BoolRef] = []
                    for req in requirements.get("req"):
                        reqs.append(generate_requisites_helper(req, mode))
                    return Or(reqs)
                case "true":
                    return BoolVal(True)
                case "false":
                    return BoolVal(False)
                case "not":
                    raise NotImplementedError("Requirements with negation have not yet been implemented")
                    req_to_negate = requirements.get("value")
                    negated_req: BoolRef = Not(self.generate_requisites(req_to_negate, semester, sophomore, junior, senior))
                    return negated_req
                case "major":
                    raise NotImplementedError("Requirements based on major have not yet been implemented")
                case _:
                    raise ValueError(f"Cannot parse type '{type}' when parsing requirements")

        requirement_expressions = []

        for mode, requirement_tree in requirements.items():
            requirement_expressions.append(
                generate_requisites_helper(
                    requirement_tree,
                    mode,
                )
            )

        return And(requirement_expressions)

    def __str__(self) -> str:
        return f"{self._id}:{self._name}:{','.join([str(ref) for ref in self._refs])}"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Course):
            return self.get_id() == other.get_id()
        return self.get_id() == other


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
        transferred_course_ids: list[str],
        desired_course_ids: list[tuple[str] | tuple[str, int]],
        undesired_course_ids: list[tuple[str] | tuple[str, int]],
        desired_degree_ids: list[str],
        courses_file_name: str = COURSES_FILE_NAME,
        degrees_file_name: str = DEGREES_FILE_NAME,
    ):
        self.ref_manager = RefManager()
        self.course_manager: CourseManager = CourseManager(semester_count)
        self.degree_manager: DegreeManager = DegreeManager()
        self.min_credits_per_semester: int = min_credit_per_semester
        self.max_credits_per_semester: int = max_credits_per_semester
        self.starts_as_fall: bool = starts_as_fall
        self.start_year: int = start_year
        self.sophomore: Rank = Rank("sophomore", first_semester_sophomore, semester_count, self.ref_manager)
        self.junior: Rank = Rank("junior", first_semester_junior, semester_count, self.ref_manager)
        self.senior: Rank = Rank("senior", first_semester_senior, semester_count, self.ref_manager)
        self.transferred_course_ids: list[str] = transferred_course_ids
        self.desired_course_ids: list[tuple[str] | tuple[str, int]] = desired_course_ids
        self.undesired_course_ids: list[tuple[str] | tuple[str, int]] = undesired_course_ids
        self.desired_degree_ids: list[str] = desired_degree_ids
        self.plan: list[list[Course]] | None = None
        self.possible_plans: list[list[list[Course]]] = []

        relevant_course_list = self._determine_relevant_courses(degrees_file_name, courses_file_name)

        self._load_courses(courses_file_name, relevant_course_list)
        self._load_degrees(degrees_file_name)

        self.degree_manager.setup(
            self.sophomore,
            self.junior,
            self.senior,
        )

        for course_id in self.transferred_course_ids:
            if not self.course_manager.by_id(course_id):
                raise Exception(f"Attempting to transfer an invalid course id '{course_id}'.")

    def _extract_known_courses(self, degrees: list[dict[Any, Any]]) -> dict[str, bool]:
        logging.debug("Extracting known course")

        def extract_degree_course(req: dict[Any, Any]):
            while req["type"] == "tag":
                req = req["node"]
            type = req["type"]
            if type == "course":
                return [f"{req['dept']} {req['number']}"]
            elif type == "all":
                return [course for opt in req["req"] for course in extract_degree_course(opt)]
            elif type == "false":
                return []
            else:
                return [course for opt in req["options"] for course in extract_degree_course(opt)]

        logging.debug("Adding courses from desired degrees")
        courses = {}
        for degree in degrees:
            for course in extract_degree_course(degree):
                courses[course] = True

        logging.debug("Adding courses from other user preference")
        for course in self.undesired_course_ids:
            courses[course[0]] = True

        for course in self.desired_course_ids:
            courses[course[0]] = True

        for course in self.transferred_course_ids:
            courses[course] = True

        return courses

    def _determine_relevant_courses(self, degrees_file_name: str, courses_file_name: str) -> set[str]:
        # self.transferred_course_ids: list[str] = transferred_course_ids
        # self.desired_course_ids: list[tuple[str] | tuple[str, int]] = desired_course_ids
        # self.undesired_course_ids: list[tuple[str] | tuple[str, int]] = undesired_course_ids
        # self.desired_degree_ids: list[str] = desired_degree_ids
        logging.debug("Determine relevant courses...")

        with open(degrees_file_name, "r") as file:
            logging.debug("Reading degree list")
            raw_degrees = json.load(file)

        degrees = []
        for id, degree in raw_degrees.items():
            if id in self.desired_degree_ids:
                degrees.append(degree)

        logging.debug("Extracted desired degrees")

        known_courses = self._extract_known_courses(degrees)

        departments = []
        for course_id in known_courses:
            if isinstance(course_id, tuple):
                course_id = course_id[0]
            departments.append(course_id.split(" ")[0])
        department_counts = Counter(departments)
        logging.debug(f"Department counts: {department_counts}")
        if len(department_counts) > 0:
            most_common_dept = department_counts.most_common()[0][0]
        else:
            most_common_dept = ""
        logging.debug(f"Calculated most common department: {most_common_dept}")

        logging.debug("Creating course requisite dictionary and adding courses from most common dept")
        course_requirement_map = {}
        with open(courses_file_name, "r") as file:
            raw_courses = json.load(file)
            for course in raw_courses:
                course_requirement_map[course["id"]] = self._extract_course_reqs(course)
                # Add in all courses from most important dept
                if course["dept"] == most_common_dept:
                    # logging.warning(f"Adding new course from dept: {course['id']}")
                    known_courses[course["id"]] = True

        previous_known_course_count = len(known_courses)
        # Add in all requisites of relevant courses
        i = 0
        while i < len(known_courses):
            course = list(known_courses.keys())[i]
            if course not in course_requirement_map:
                i += 1
                continue
            reqs = course_requirement_map[course]
            for req in reqs:
                known_courses[req] = True
            i += 1
        after_known_course_count = len(known_courses)
        increase_in_known_course_count = after_known_course_count - previous_known_course_count
        logging.info(f"Increase course count by {increase_in_known_course_count} when adding reqs")

        if after_known_course_count > 100:
            logging.warning(f"Relevant course count is {after_known_course_count} for {', '.join(self.desired_degree_ids)}")

        return set(known_courses.keys())

    def _extract_course_reqs(self, course: dict[Any, Any]) -> list[str]:
        # logging.debug(f"Extracting course reqs for {course['dept']} {course['number']} {course['name']}")

        def extract_course_reqs_helper(items: dict[Any, Any]):
            type = items["type"]
            if type == "all" or type == "some":
                # logging.debug(f"Determined type all/some for {items}")
                return [id for value in items["req"] for id in extract_course_reqs_helper(value)]
            elif type == "course":
                # logging.debug(f"Determined type course for {items}")
                return [f"{items['dept']} {items['number']}"]
            elif type == "true" or type == "standing":
                return []
            raise ValueError(f"Failed to extract course reqs for {items}. Unexpected type: '{type}'")

        full_requirement_list = []
        for requirement_type in ["prereq", "preorco", "coreq"]:
            requirements = extract_course_reqs_helper(course[requirement_type])
            full_requirement_list.extend(requirements)
            # logging.info(f"{course['dept']} {course['number']} {course[requirement_type]} --> {requirements}")
        return full_requirement_list

    def _load_courses(self, file_name: str, relevant_course_list: set[str]) -> None:
        with open(file_name, "r") as file:
            raw_courses = json.load(file)

        for raw_course in raw_courses:
            if raw_course["id"] in relevant_course_list:
                self.course_manager.add_course(Course(**raw_course, course_manager=self.course_manager, ref_manager=self.ref_manager, starts_as_fall=self.starts_as_fall, start_year=self.start_year))

    def _load_degrees(self, file_name: str) -> None:
        with open(file_name, "r") as file:
            raw_degrees = json.load(file)

        for name, requirements in raw_degrees.items():
            if name in self.desired_degree_ids:
                self.degree_manager.add_degree(
                    Degree(
                        name=name,
                        id=name,
                        requirements=requirements,
                        course_manager=self.course_manager,
                        ref_manager=self.ref_manager,
                    )
                )

        # for degree in self.degree_manager:
        #    logging.debug(degree)

    def setup(self) -> None:
        self.solver = Optimize()

        self._generate_bootstrap()

        non_credit_courses = []

        for course in self.course_manager:
            logging.debug(f"Applying cnf for {course.get_id()} {course.get_name()}...")
            course.apply_cnf(self.solver, self.sophomore, self.junior, self.senior)

            if course.is_variable_credits() and course.get_credits() == 0:
                non_credit_courses.extend(course.get_refs()[1:])

        # We always want to avoid adding tons of 0 credit courses
        if len(non_credit_courses) > 0:
            self.solver.minimize(sum(non_credit_courses))

        self._add_desired_courses()
        self._add_undesired_courses()

        self._add_semester_credit_requirements()

        self._add_degree_reqs()

    def _generate_bootstrap(self) -> None:
        self._generate_transfer_bootstrap()
        self._generate_rank_bootstrap()

    def _generate_transfer_bootstrap(self) -> None:
        transfer_courses: list[BoolRef] = []
        for course in self.course_manager:
            if course.get_id() in self.transferred_course_ids:
                transfer_courses.append(course.at(0))
            else:
                transfer_courses.append(Not(course.at(0)))
        self.solver.add(And(transfer_courses))

    def _generate_rank_bootstrap(self) -> None:
        rank_bootstrap: list[BoolRef] = []
        for rank in (self.sophomore, self.junior, self.senior):
            rank_bootstrap.extend(rank.generate_bootstrap())
        self.solver.add(And(rank_bootstrap))

    def _add_desired_courses(self) -> None:
        desired_refs = []
        for pair in self.desired_course_ids:
            id: str = pair[0]
            course = self.course_manager.by_id(id)
            count: int | None = pair[1] if len(pair) > 1 else None
            if count is None:
                desired_refs.append(course.at(1, self.course_manager.get_semester_count()))
            else:
                desired_refs.append(course.at(count, count))

        # NOTE: This *possibly* could be made into a soft constraint if we want
        # to return good courses even if invalid desire. Probably best to not
        # return anything if we cannot meet all desires though
        self.solver.add(And(desired_refs))

    def _add_undesired_courses(self) -> None:
        undesired_refs = []
        for pair in self.undesired_course_ids:
            id: str = pair[0]
            course = self.course_manager.by_id(id)
            count: int | None = pair[1] if len(pair) > 1 else None
            if count is None:
                undesired_refs.append(And([Not(course.at(i, i)) for i in range(1, self.course_manager.get_semester_count() + 1)]))
            else:
                undesired_refs.append(Not(course.at(count, count)))

        # NOTE: This *possibly* could be made into a soft constraint if we want
        # to return good courses even if invalid desire. Probably best to not
        # return anything if we cannot meet all desires though
        self.solver.add(And(undesired_refs))

    def _add_semester_credit_requirements(self) -> None:
        for semester in range(1, self.course_manager.get_semester_count() + 1):
            refs: list[BoolRef] = [course.at(semester) for course in self.course_manager]
            weights: list[int | ArithRef] = [course.get_credits() for course in self.course_manager]

            # Upper bound
            self.solver.add(sum([weight * ref for weight, ref in zip(weights, refs)]) <= self.max_credits_per_semester)

            # Lower bound
            self.solver.add(sum([weight * ref for weight, ref in zip(weights, refs)]) >= self.min_credits_per_semester)

    # TODO: Implementation might be weird with courses requiring you have a specific
    # major, when not all majors have references.
    def _add_degree_reqs(self) -> None:
        for degree_id in self.desired_degree_ids:
            self.solver.add(self.degree_manager.by_id(degree_id).generate_cnf())

        for course in self.course_manager:
            self.solver.add(course.generate_taken_requirement_cnf())

    # WARNING: Be careful, somethings this makes things take forever, right now
    # it seems to be behaving itself though
    def minimize(self) -> None:
        refs = [[] for _ in range(self.course_manager.get_semester_count())]
        for course in self.course_manager:
            for i, ref in enumerate(course.get_refs()[1:]):
                refs[i].append(ref)

        c = 0
        for sem in reversed(refs):
            self.solver.minimize(sum(sem))
            c += 1

    def solve_all(self) -> None:
        while self.solve():
            pass

    # TODO: Could implement a pseudo-minimization by after we solve it, going through
    # and setting each variable to false then seeing if you are still sat.
    # Somehow  you have to make sure it doesn't just as a ton of other classes
    # though... not sure how to do that part
    def solve(self) -> bool:
        negation_of_current_solution = []
        self.plan = [[] for _ in range(self.course_manager.get_semester_count() + 1)]  # TODO: Fix the semester count here

        # for k, v in RefManager.store.items():
        #    logging.debug(f"{k}: {v}")

        logging.debug("Attempting to solve")
        if self.solver.check() == sat:
            logging.info(f"SAT - {', '.join(self.desired_degree_ids)}")
            model: ModelRef = self.solver.model()

            for funcDeclRef in model.decls():
                ref: BoolRef | ArithRef = funcDeclRef()
                if isinstance(ref, ArithRef):
                    # Ignore specific values of credit counts for variable credit courses
                    continue

                boolRef: BoolRef = ref

                if not isinstance(boolRef, BoolRef):
                    raise TypeError(f"Expected model to only consist of BoolRefs, instead got '{funcDeclRef}'")

                reference_result: Any = self.ref_manager.get(boolRef)
                if isinstance(reference_result, Course):
                    # logging.debug(f"{boolRef} != {model[boolRef]}")
                    negation_of_current_solution.append(boolRef != model[boolRef])
                    course: Course = reference_result
                    semester: int = course.get_refs().index(boolRef)

                    if model[boolRef]:
                        self.plan[semester].append(course)

            self.possible_plans.append(self.plan)
            self.solver.add(Or(negation_of_current_solution))
            return True

        else:
            logging.info(f"UNSAT - {', '.join(self.desired_degree_ids)}")
            return False

    def get_plans_with_ids(self) -> list[list[Any]]:
        plans = []
        for plan in self.possible_plans:
            plans.append(self.get_plan_with_ids(plan))
        return plans

    def get_plan_with_ids(self, plan: list[list[Course]] | None = None) -> list[Any]:
        plan = plan or self.plan
        if plan is None:
            raise Exception("Cannot get plan ids for an empty plan")
        possible_plans = []
        for semester in plan:
            courses = [course.get_id() for course in semester]
            possible_plans.append(courses)
        return possible_plans

    def display(self) -> None:
        if self.plan is None or len(self.possible_plans) == 0:
            logging.warning("CourseSATSolver needs to be solved before a plan can be displayed")
            return

        for plan_id, plan in enumerate(self.possible_plans):
            logging.info(f"Plan {plan_id + 1}:")
            for i, semester in enumerate(plan):
                semester_name: str
                if i == 0:
                    semester_name = "Transferred"
                else:
                    semester_name = self._get_semester_name(i)
                logging.info(f"Semester {i}: {semester_name}")
                for course in sorted(semester, key=lambda course: course.get_id()):
                    logging.info(f"\t{course}")

    def _get_semester_name(self, semester: int) -> str:
        season: str
        year: int
        if self.starts_as_fall:
            season = "Fall" if semester % 2 == 1 else "Spring"
            year = self.start_year + (semester // 2)
        else:
            season = "Spring" if semester % 2 == 1 else "Fall"
            year = self.start_year + ((semester - 1) // 2)
        return f"{season} {year}"


if __name__ == "__main__":
    ##########################
    ### START CONFIG VARIABLES
    ##########################
    # These will all be taken as input from the user

    with open(os.path.join(DATA_DIR, "degree-names"), "r") as infile:
        degree_names = [line.strip() for line in infile.readlines()]

    degrees = []
    for degree in degree_names:
        if degree in [
            "POLITICAL SCIENCE BA (2008-present)   940BA",
            "HISTORY: GLOBAL STUDIES BA  (2024-2025) 963BA",
            "SOCIAL WORK BSW (2024-2025)  450BSW",
            "MATERIALS SCIENCE AND ENGINEERING BS (2024-PRESENT) 35BBS",
            "MATERIALS SCIENCE ENGINEERING TECHNOLOGY BS (2024-PRESENT) 35CBS",  # Huh, this is different
            "SOCIAL SCIENCE TEACHING - PLAN B - All Social Science  (2024-2025)  90BBAT",  # Solvable but a little bit slower
            "THEATRE: THEATRE FOR YOUTH AND COMMUNITIES BA MAJOR (2024-PRESENT) 49FBA",
            "RELIGIOUS STUDIES BA MAJOR (2024-PRESENT) 641BA",
            "PHILOSOPHY BA MAJOR (2024-PRESENT) 650BA",
            "EARLY CHILDHOOD EDUCATION TEACHING BA (2022-2025) 210BAT",
            "ECONOMICS: APPLIED ECONOMIC ANALYSIS  (2023-present)  926BA",
            "GEOGRAPHY BA  (2022-present)   97RBA",
            "PSYCHOLOGY BA MAJOR  (2023-2025) 400BA",
            "GERONTOLOGY: SOCIAL SCIENCE TRACK MAJOR (2023-2025) 31SBA",
            "FAMILY SERVICES BA MAJOR (2024-2025) 31FBA",
            "ENVIRONMENTAL RESOURCE MANAGEMENT- ENV. COMPLIANCE (2024-present) 97PBA",
            "HISTORY TEACHING BA (2024-2025) 960BAT",
            "COMMUNICATION DISORDERS BA MAJOR (2023-PRESENT) 512BA",
            "HISTORY BA (2024-present) 960BA",
            "PUBLIC HEALTH (2024-2025) 41BBA",
            "PHYSICAL EDUCATION TEACHING MAJOR  (2022-2025)  420BAT",
            "PUBLIC ADMINISTRATION BA MAJOR (2023-present) 94XBA",
            "SOCIOLOGY BA MAJOR (2023-2025)   980BA",
            "AUTOMATION ENGINEERING TECHNOLOGY BS (2024-present) - 35ABS",
            "MECHANICAL ENGINEERING TECHNOLOGY BS (2024-PRESENT) 35DBS",
            "THEATRE: DESIGN AND PRODUCTION BA MAJOR (2024-PRESENT) 49PBA",
            "THEATRE: PERFORMANCE BA MAJOR (2024-PRESENT) 49CBA",
            "PERFORMANCE BM: VOCAL TRACK (2020-PRESENT)    52LBM",
            "PERFORMANCE BM: JAZZ STUDIES TRACK (2024-PRESENT)  52KBM",
            "COMPOSITION BM (2024-PRESENT)  52UBM",
            "MUSIC: GENERAL STUDIES IN MUSIC BA  (2017-present)   5T1BA",
            "MUSIC: JAZZ STUDIES BA MAJOR (2017-present)   5T2BA",
            "MUSIC: STRING PEDAGOGY BA MAJOR (2017-present)   5T3BA",
            "MUSIC: PERFORMING ARTS MANAGEMENT BA MAJOR (2023-present)  5T4BA",
            "MUSIC: MUSIC TECHNOLOGY BA MAJOR (2020-2025)  5T5BA",
            "MUSIC: MUSIC HISTORY BA MAJOR (2020-present)   5T6BA",
            "STATISTICS AND ACTUARIAL SCIENCE BA MAJOR (2024-present) 80RBA",
            "BIOLOGY BS MAJOR (2024-present) 84ABS",
            "BIOLOGY:ECOLOGY/EVOLUTION&ORGANISMAL HONORS RESEARCH BA MAJOR(2024-2025)84JBA",
            "BIOLOGY BA MAJOR (2024-present) 84KBA",
            "BIOLOGY 3+1 JOINT BA MAJOR (2024-present) 84NBA",
            "PHYSICS: CUSTOM EMPHASIS BA MAJOR (2024-present) 88BBA",
            "KINESIOLOGY MAJOR: EXERCISE SCIENCE EMPHASIS (2024-present) 42UBA",
            "COMPREHENSIVE SECONDARY SCIENCE TEACHING (2020-2025) 82ABAT",
            "BIOLOGY TEACHING BA MAJOR (2024-2025) 844BAT",
            "EARTH SCIENCE TEACHING BA MAJOR (2020-2025) 870BAT",
            "PHYSICS BA TEACHING MAJOR (2020-2025) 880BAT",
            "MARKETING: MARKETING MANAGEMENT BA (2023-2025) 13KBA",
            "MANAGEMENT INFORMATION SYSTEMS BA (2024-2025) 14DBA",
            "HUMAN RESOURCE MANAGEMENT BA (2023-2025) 15TBA",
            "MANAGEMENT: BUSINESS ADMINISTRATION BA (2023-2025)  15DBA",
            "SUPPLY CHAIN MANAGEMENT BA (2023-2025)  15SBA",
            "ACCOUNTING BA (2023-2025)  152BA",
            "FINANCE: FINANCIAL MANAGEMENT BA (2023-2025)  16FBA",
            "REAL ESTATE BA (2023-2025) 166BA",
            "INTERNATIONAL BUSINESS MINOR (2024-present)  101MIN",
            "ENTREPRENEURSHIP MINOR (2024-2025) 131MIN",
            "MARKETING MINOR (2024-present)  15NMIN",
            "REAL ESTATE - BUSINESS MINOR (2022-2025)  16BMIN",
            "FINANCE MINOR - For Business Majors (2023-2025) 16CMIN",
            "CYBERSECURITY AND SYSTEM ADMINISTRATION BS MAJOR (2024-present) 81MBS",
            "COMPUTER SCIENCE BS MAJOR (2016-2025) 81SBS",
            "UNI BACHELOR OF SCIENCE NURSING (2024-2025) 41RBSN",
            "GERONTOLOGY: LONG TERM CARE ADMINISTRATION (2023-present) 31LBA",
            "MENTAL HEALTH MINOR (2024-present)  406MIN",
            "KINESIOLOGY MAJOR: PRE-HEALTH EMPHASIS (2024-present) 42VBA",
            "PERFORMANCE BM: INSTRUMENTAL TRACK A (2021-PRESENT)   52HBM",
            "GEOGRAPHIC INFORMATION SCIENCE BS  (2024-present)   97SBS",
        ]:
            continue
        degrees.append(degree)

    # degrees = ["COMPUTER SCIENCE BS MAJOR (2016-2025) 81SBS"]
    degrees = ["COMPUTER SCIENCE BA MAJOR (2016-2025) 810BA"]

    for degree in degrees:
        logging.info(f"Running for {degree}...")
        c: CourseSATSolver = CourseSATSolver(
            semester_count=8,  # Number of semester to calculate for
            min_credit_per_semester=12,  # Minimum credits (inclusive)
            max_credits_per_semester=18,  # Maximum credits (inclusive)
            starts_as_fall=True,
            start_year=2025,
            transferred_course_ids=[],
            desired_course_ids=[],
            undesired_course_ids=[],
            desired_degree_ids=[degree],
            first_semester_sophomore=3,  # NOTE: One-indexed!
            first_semester_junior=5,
            first_semester_senior=7,
        )

        c.setup()
        logging.info("Finished setup")
        # c.minimize()
        # logging.info("Added minimization")

        try:
            if c.solve():
                c.display()
            else:
                logging.error(f"No valid schedule for '{degree}'")
        except Exception as e:
            logging.error(f"Received error {e} when trying to schedule {degree}")
