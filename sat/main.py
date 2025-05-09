from enum import StrEnum
import json
from typing import Any, Generator, TypeVar, override

from typeguard import typechecked
from z3 import Implies
from z3.z3 import And, Bool, BoolRef, BoolVal, ModelRef, Not, Optimize, Or, sat  # type: ignore[import-untyped]

from config import COURSES_FILE_NAME, DEGREES_FILE_NAME

from degree_requirement_manager import DegreeRequirementManager


@typechecked
class Offering(StrEnum):
    FALL = "FALL"
    SPRING = "SPRING"
    FALL_AND_SPRING = "FALL AND SPRING"
    VARIABLE = "VARIABLE"
    EVEN_FALLS = "EVEN FALLS"
    ODD_FALLS = "ODD FALLS"
    EVEN_SPRINGS = "EVEN SPRINGS"
    ODD_SPRINGS = "ODD SPRINGS"
    FALL_SPRING_SUMMER = "FALL, SPRING, SUMMER"
    SUMMER = "SUMMER"


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
            degree.get_requirements().setup(Course, Degree, sophomore, junior, senior)
            print("Printing degree requirement classes:")
            for course in degree.get_requirements().get_courses():
                print(f"\t{course._name}")

    def add_degree(self, degree: "Degree"):
        if degree.get_id() in self.degrees:
            raise KeyError(f"Key {degree.get_id()} already exists in degree list")

        self.degrees[degree.get_id()] = degree

    def by_id(self, id: Any) -> "Degree":
        if id not in self.degrees:
            raise IndexError(f"Unable to find id '{id}' in courses")
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
        requirements: dict[Any, Any] = {},
    ):
        self._id: Any = id
        self._name: str = name
        self._ref = RefManager.allocate(self)
        self._requirements: DegreeRequirementManager = DegreeRequirementManager(course_manager, requirements)

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
    def __init__(self, name: str, first_semester_with_rank: int | None, semester_count: int):
        self._name: str = name
        self._first_semester_with_rank: int | None = first_semester_with_rank
        self._refs: list[BoolRef] = []
        self._semester_count: int = semester_count
        for _ in range(semester_count):
            self._refs.append(RefManager.allocate(self))

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

        self._courses[course.get_id()] = course

    def __iter__(self) -> Generator["Course", Any, None]:
        yield from self._courses.values()

    def by_id(self, id: Any) -> "Course":
        if id not in self._courses:
            raise IndexError(f"Unable to find id '{id} in courses")
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
        self._id: Any = id.upper()  # TODO: Ideally get rid of this
        self._requirements: Any = {
            "prereq": prereq,
            "coreq": coreq,
            "preorco": preorco,
        }
        self._dept: str = dept.upper()  # TODO: Ideally get rid of this
        self._number: str = number
        # TODO: This is not the best solution, but works for now
        self._credits: int = hours[0]
        self._credits_repeatable_for: int | None = credits_repeatable_for
        self._starts_as_fall = starts_as_fall
        self._start_year = start_year
        self._season: Offering = Offering(semester.upper())
        self._refs: list[BoolRef] = []
        self._taken_for_specific_rg: list[BoolRef] = []
        self._course_manager: CourseManager = course_manager
        for _ in range(self._course_manager.get_semester_count() + 1):  # +1 because allows a slot for transfer credits
            self._refs.append(RefManager.allocate(self))

    def get_id(self) -> Any:
        return self._id

    def get_name(self) -> str:
        return self._name

    def get_refs(self) -> list[BoolRef]:
        return self._refs

    def get_credits(self) -> int:
        return self._credits

    # TODO: Make sure this is right
    def add_as_degree_req(self) -> BoolRef:
        ref = RefManager.allocate(None)
        self._taken_for_specific_rg.append(ref)
        return ref

    def generate_taken_requirement_cnf(self) -> BoolRef:
        requirements: list[BoolRef] = []

        # If taken for credit, it has to be taken!
        for taken_for_specific_rg in self._taken_for_specific_rg:
            requirements.append(Implies(taken_for_specific_rg, Or(self.at())))

        # Cannot take for credit multiple places
        requirements.append(sum(self._taken_for_specific_rg) <= 1)

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
        solver.add(self._generate_seasonal_requirements())
        solver.add(self._generate_requisite_cnf(sophomore, junior, senior))
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
            case Offering.ODD_FALLS:
                offering_list = [True, False, False, False]
            case Offering.EVEN_FALLS:
                offering_list = [False, False, True, False]
            case Offering.SPRING:
                offering_list = [False, True, False, True]
            case Offering.ODD_SPRINGS:
                offering_list = [False, False, False, True]
            case Offering.EVEN_SPRINGS:
                offering_list = [False, True, False, False]
            case Offering.FALL_AND_SPRING | Offering.VARIABLE:
                offering_list = [True, True, True, True]

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
            print(requirements, mode)
            if len(requirements) == 0:
                return

            type = requirements.get("type")

            course: Course

            match type:
                case "course":
                    course_id = requirements.get("dept").upper() + " " + requirements.get("number")
                    try:
                        course = self._course_manager.by_id(course_id)
                    except Exception as e:
                        print(e)
                        print("However, we keep moving...")
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
                    else:
                        raise ValueError(f"Invalid rank {standing} detected while parsing requirements")
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
        plan_file_name: str = "placeholder_name.txt",
    ):
        self.course_manager: CourseManager = CourseManager(semester_count)
        self.degree_manager: DegreeManager = DegreeManager()
        self.semester_count: int = semester_count
        self.min_credits_per_semester: int = min_credit_per_semester
        self.max_credits_per_semester: int = max_credits_per_semester
        self.starts_as_fall: bool = starts_as_fall
        self.start_year: int = start_year
        self.first_semester_sophomore: int = first_semester_sophomore
        self.sophomore: Rank = Rank("sophomore", first_semester_sophomore, semester_count)
        self.first_semester_junior: int = first_semester_junior
        self.junior: Rank = Rank("junior", first_semester_junior, semester_count)
        self.first_semester_senior: int = first_semester_senior
        self.senior: Rank = Rank("senior", first_semester_senior, semester_count)
        self.transferred_course_ids: list[str] = transferred_course_ids
        self.desired_course_ids: list[tuple[str] | tuple[str, int]] = desired_course_ids
        self.undesired_course_ids: list[tuple[str] | tuple[str, int]] = undesired_course_ids
        self.desired_degree_ids: list[str] = desired_degree_ids
        self.plan: list[list[Course]] | None = None
        self.possible_plans: list[list[list[Course]]] = []

        self._load_courses(courses_file_name)
        self._load_degrees(degrees_file_name)

        self.degree_manager.setup(
            self.sophomore,
            self.junior,
            self.senior,
        )

        for course_id in self.transferred_course_ids:
            if not self.course_manager.by_id(course_id):
                raise Exception(f"Attempting to transfer an invalid course id '{course_id}'.")

    def _load_courses(self, file_name: str) -> None:
        with open(file_name, "r") as file:
            raw_courses = json.load(file)

        for raw_course in raw_courses:
            self.course_manager.add_course(Course(**raw_course, course_manager=self.course_manager, starts_as_fall=self.starts_as_fall, start_year=self.start_year))

    def _load_degrees(self, file_name: str) -> None:
        with open(file_name, "r") as file:
            raw_degrees = json.load(file)["degrees"]

        for raw_degree in raw_degrees:
            self.degree_manager.add_degree(Degree(**raw_degree, course_manager=self.course_manager))

        # for degree in self.degree_manager:
        #    print(degree)

    def setup(self) -> None:
        self.solver = Optimize()

        self._generate_bootstrap()

        for course in self.course_manager:
            print(f"Applying cnf for {course.get_name()}...")
            course.apply_cnf(self.solver, self.sophomore, self.junior, self.senior)

        self._add_desired_courses()
        self._add_undesired_courses()

        self._add_semester_credit_requirements()

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
            weights: list[int] = [course.get_credits() for course in self.course_manager]

            # Upper bound
            self.solver.add(sum([weight * ref for weight, ref in zip(weights, refs)]) <= self.max_credits_per_semester)

            # Lower bound
            self.solver.add(sum([weight * ref for weight, ref in zip(weights, refs)]) >= self.min_credits_per_semester)

    # TODO: Implementation might be weird with courses requiring you have a specific
    # major, when not all majors have references.
    def add_degree_reqs(self) -> None:
        for degree_id in self.desired_degree_ids:
            self.solver.add(self.degree_manager.by_id(degree_id).generate_cnf())

        for course in self.course_manager:
            self.solver.add(course.generate_taken_requirement_cnf())

    # WARNING: Be careful, somethings this makes things take forever, right now
    # it seems to be behaving itself though
    def minimize(self) -> None:
        refs = []
        for course in self.course_manager:
            refs.extend(course.get_refs())

        self.solver.minimize(sum(refs))

    # TODO: Could implement a pseudo-minimization by after we solve it, going through
    # and setting each variable to false then seeing if you are still sat.
    # Somehow  you have to make sure it doesn't just as a ton of other classes
    # though... not sure how to do that part
    def solve(self) -> bool:
        negation_of_current_solution = []
        self.plan = [[] for _ in range(self.course_manager.get_semester_count() + 1)]  # TODO: Fix the semester count here

        # for k, v in RefManager.store.items():
        #    print(f"{k}: {v}")

        if self.solver.check() == sat:
            print("SAT")
            model: ModelRef = self.solver.model()

            for funcDeclRef in model.decls():
                boolRef: BoolRef = funcDeclRef()
                if not isinstance(boolRef, BoolRef):
                    raise TypeError(f"Expected model to only consist of BoolRefs, instead got '{funcDeclRef}'")

                reference_result: Any = RefManager.get(boolRef)
                if isinstance(reference_result, Course):
                    print(f"{boolRef} != {model[boolRef]}")
                    negation_of_current_solution.append(boolRef != model[boolRef])
                    course: Course = reference_result
                    semester: int = course.get_refs().index(boolRef)

                    if model[boolRef]:
                        self.plan[semester].append(course)

            self.possible_plans.append(self.plan)
            self.solver.add(Or(negation_of_current_solution))
            return True

        else:
            print("UNSAT")
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
        plan = []
        for semester in self.plan:
            courses = [course.get_id() for course in semester]
            plan.append(courses)
        return plan

    def display(self) -> None:
        if self.plan is None:
            raise ValueError("CourseSATSolver needs to be solver before a plan can be displayed")
        if len(self.possible_plans) == 0:
            raise ValueError("CourseSATSolver needs at least 1 valid solution before a plan can be displayed")

        for plan_id, plan in enumerate(self.possible_plans):
            print(f"\nPlan {plan_id + 1}:")
            for i, semester in enumerate(plan):
                semester_name: str
                if i == 0:
                    semester_name = "Transferred"
                else:
                    semester_name = self._get_semester_name(i)
                print(f"Semester {i}: {semester_name}")
                for course in sorted(semester, key=lambda course: course.get_id()):
                    print(f"\t{course}")


    
    def savefile(self) -> None:
        if self.plan is None:
            raise ValueError("CourseSATSolver needs to be solver before a plan can be saved")
        if len(self.possible_plans) == 0:
            raise ValueError("CourseSATSolver needs at least 1 valid solution before a plan can be saved")
        dateTimeNow = str(datetime.datetime.now())
        dateTimeNow = dateTimeNow.replace(':','.')
        path = "plans"
        if not os.path.exists(path):
            os.makedirs(path)
        
        for plan_id, plan in enumerate(self.possible_plans):
            filename = "Plan" + str(plan_id + 1) + "-" + dateTimeNow + ".txt"
            self.plan_file_name = filename
            with open(os.path.join(path, filename),"w") as f:
                f.write(f"{filename}")
            with open(os.path.join(path, filename),"a") as f:
                f.write(f"\nInput-")
                f.write(f"\nSemester Count: {self.semester_count}")
                f.write(f"\nMinimum Credits Per Semester: {self.min_credits_per_semester}")
                f.write(f"\nMaximum Credits Per Semester: {self.max_credits_per_semester}")
                f.write(f"\nStart as Fall: {self.starts_as_fall}")
                f.write(f"\nStart Year: {self.start_year}")
                f.write(f"\nTransferred Courses: {self.transferred_course_ids}")
                f.write(f"\nDesired Courses: {self.desired_course_ids}")
                f.write(f"\nUndesired Courses: {self.undesired_course_ids}")
                f.write(f"\nDesired Degrees: {self.desired_degree_ids}")
                f.write(f"\nFirst Semester Sophomore: {self.first_semester_sophomore}")
                f.write(f"\nFirst Semester Junior: {self.first_semester_junior}")
                f.write(f"\nFirst Semester Senior: {self.first_semester_senior}")
                f.write(f"\n \nOutput-")
            for i, semester in enumerate(plan):
                semester_name: str
                if i == 0:
                    semester_name = "Transferred"
                else:
                    semester_name = self._get_semester_name(i)
                with open(os.path.join(path, filename),"a") as f:
                    f.write(f"\nSemester {i}: {semester_name}")
                for course in sorted(semester, key=lambda course: course.get_id()):
                    with open(os.path.join(path, filename),"a") as f:
                        f.write(f"\n\t{course}")

    
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
    c: CourseSATSolver = CourseSATSolver(
        semester_count=4,  # Number of semester to calculate for
        min_credit_per_semester=3,  # Minimum credits (inclusive)
        max_credits_per_semester=16,  # Maximum credits (inclusive)
        starts_as_fall=True,
        start_year=2025,
        transferred_course_ids=[],  # ["CS1410", "CS1510"],
        desired_course_ids=[
            # ("CS3430/5430", 4),
            # ("CS1160",),
        ],
        undesired_course_ids=[
            # ("CS4410/5410",),
        ],
        desired_degree_ids=["CS:BA"],
        first_semester_sophomore=1,  # NOTE: One-indexed!
        first_semester_junior=1,
        first_semester_senior=1,
    )
    ########################
    ### END CONFIG VARIABLES
    ########################

    c.setup()
    c.add_degree_reqs()
    c.minimize()

    c.solve()
    c.display()
    c.safefile()

    # while c.solve():
    #    pass

    # plan_ids = []
    # for plan in c.possible_plans:
    #    semester_ids = []
    #    for semester in plan:
    #        courses = [c.get_id() for c in semester]
    #        semester_ids.append(courses)
    #    plan_ids.append(semester_ids)
    # print(plan_ids)
    #
    # print(c.possible_plans)
    # c.display()
