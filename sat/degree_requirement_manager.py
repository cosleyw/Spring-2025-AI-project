from typeguard import typechecked
from typing import Any, override
from abc import abstractmethod
import z3.z3 as z3
import logging
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


@typechecked
class DegreeRequirement:
    def __init__(self):
        self._id: UUID = uuid4()

    def get_id(self) -> UUID:
        return self._id

    @abstractmethod
    def eval(self) -> z3.BoolRef:
        pass

    @abstractmethod
    def get_courses(self) -> list[Any]:
        pass

    @abstractmethod
    def get_nodes(self) -> list["DegreeRequirement"]:
        pass


@typechecked
class CreditRange(DegreeRequirement):
    def __init__(self, n: int, m: int, items: list[DegreeRequirement], required: bool = False):
        super().__init__()
        self._min: int = n
        self._max: int = m
        self._items: list[DegreeRequirement] = items
        self._required = required

        if self._min > self._max:
            raise ValueError(f"Minimum credits required ({self._min}) cannot exceeed maximum credits required ({self._max}) for a degree")

        if self._max <= 0:
            raise ValueError("Cannot use CreditRange with max <= 0; receieved max='{self._max}'")

    @override
    def get_courses(self) -> list[Any]:
        courses = []
        for item in self._items:
            courses.extend(item.get_courses())
        return courses

    @override
    def get_nodes(self) -> list["DegreeRequirement"]:
        nodes: list["DegreeRequirement"] = [self]
        for item in self._items:
            nodes.extend(item.get_nodes())
        return nodes

    @override
    def eval(self) -> z3.BoolRef:
        # We require that the sum of all courses matches our range
        all_courses = [course.get_credits() * course.eval() for course in self.get_nodes() if isinstance(course, ReqCourse)]
        # and we meet all other requirements
        recursive_requirements = [item.eval() for item in self._items if not isinstance(item, ReqCourse)]

        if not self._required:
            return z3.Or(
                [
                    z3.And(
                        [
                            sum(all_courses) >= self._min,
                            sum(all_courses) <= self._max,
                            *recursive_requirements,
                        ]
                    ),
                    sum(all_courses) == 0,
                ],
            )
        else:
            return z3.And(
                [
                    sum(all_courses) >= self._min,
                    sum(all_courses) <= self._max,
                    *recursive_requirements,
                ]
            )


@typechecked
class CourseRange(DegreeRequirement):
    def __init__(self, n: int, m: int, items: list[DegreeRequirement], required: bool = False):
        super().__init__()
        self._min: int = n
        self._max: int = m
        self._items: list[DegreeRequirement] = items
        self._required = required

        if self._min > self._max:
            raise ValueError(f"Minimum courses required ({self._min}) cannot exceeed maximum courses required ({self._max}) for a degree")

        # Can no longer make this assertion since counts are determined recursively
        # if len(self._items) < self._min:
        #    raise ValueError(f"Cannot require {self._min} be taken from (len={len(self._items)}) items '{self._items}'")

        if self._max <= 0:
            raise ValueError("Cannot use CourseRange with max <= 0; receieved max='{self._max}'")

    @override
    def get_courses(self) -> list[Any]:
        courses = []
        for item in self._items:
            courses.extend(item.get_courses())
        return courses

    @override
    def get_nodes(self) -> list["DegreeRequirement"]:
        nodes: list["DegreeRequirement"] = [self]
        for item in self._items:
            nodes.extend(item.get_nodes())
        return nodes

    @override
    def eval(self) -> z3.BoolRef:
        # We require that the sum of all courses matches our range
        all_courses = [course.eval() for course in self.get_nodes() if isinstance(course, ReqCourse)]
        # and we meet all other requirements
        recursive_requirements = [item.eval() for item in self._items if not isinstance(item, ReqCourse)]

        if not self._required:
            return z3.Or(
                [
                    z3.And(
                        [
                            sum(all_courses) >= self._min,
                            sum(all_courses) <= self._max,
                            *recursive_requirements,
                        ],
                    ),
                    sum(all_courses) == 0,
                ]
            )
        else:
            return z3.And(
                [
                    sum(all_courses) >= self._min,
                    sum(all_courses) <= self._max,
                    *recursive_requirements,
                ]
            )


@typechecked
class All(DegreeRequirement):
    def __init__(self, items: list[DegreeRequirement], required: bool = False):
        super().__init__()
        self._items: list[DegreeRequirement] = items
        self._required = required

    @override
    def get_courses(self) -> list[Any]:
        courses = []
        for item in self._items:
            courses.extend(item.get_courses())
        return courses

    @override
    def get_nodes(self) -> list["DegreeRequirement"]:
        nodes: list["DegreeRequirement"] = [self]
        for item in self._items:
            nodes.extend(item.get_nodes())
        return nodes

    @override
    def eval(self) -> z3.BoolRef:
        # and we meet all other requirements
        recursive_requirements = [item.eval() for item in self._items if not isinstance(item, ReqCourse)]

        if not self._required:
            return z3.Or([z3.And(recursive_requirements), sum(recursive_requirements) == 0])
        else:
            return z3.And(recursive_requirements)


@typechecked
class ReqTrue(DegreeRequirement):
    def __init__(self):
        self._id: UUID = uuid4()

    def get_id(self) -> UUID:
        return self._id

    @abstractmethod
    def eval(self) -> z3.BoolRef:
        return z3.BoolVal(True)

    @abstractmethod
    def get_courses(self) -> list[Any]:
        return []

    @abstractmethod
    def get_nodes(self) -> list["DegreeRequirement"]:
        return [self]


@typechecked
class ReqFalse(DegreeRequirement):
    def __init__(self):
        self._id: UUID = uuid4()

    def get_id(self) -> UUID:
        return self._id

    @abstractmethod
    def eval(self) -> z3.BoolRef:
        return z3.BoolVal(False)

    @abstractmethod
    def get_courses(self) -> list[Any]:
        return []

    @abstractmethod
    def get_nodes(self) -> list["DegreeRequirement"]:
        return [self]


@typechecked
class ReqCourse(DegreeRequirement):
    def __init__(self, course, degree_id):
        super().__init__()
        self._course = course
        self._ref = course.add_as_degree_req(degree_id)

    @override
    def get_courses(self) -> list[Any]:
        return [self._course]

    @override
    def get_nodes(self) -> list[DegreeRequirement]:
        return [self]

    @override
    def eval(self) -> z3.BoolRef:
        return self._ref

    def get_credits(self) -> int | z3.z3.ArithRef:
        return self._course.get_credits()


# TODO: Implement degree requirements
@typechecked
class DegreeRequirementManager:
    def __init__(
        self,
        course_manager,
        degree_id: str,
        requirements: dict[Any, Any],
    ):
        self._raw_requirements = requirements
        self._degree_id: str = degree_id
        self._requirements: DegreeRequirement
        self._course_manager = course_manager

    def setup(self) -> None:
        self._requirements = self._parse_recursive(self._raw_requirements)

    # TODO: Delete this method, it was only here for testing
    def get_courses(self):
        return self._requirements.get_courses()

    def _parse_recursive(self, requirements: Any) -> DegreeRequirement:
        def parse_recursive_helper(requirements: Any, required=False):
            type = requirements.get("type")
            # TODO: Can change this back to recrusive call with req.get(node) as requirements
            while type == "tag":
                requirements = requirements.get("node")
                type = requirements.get("type")

            if type == "course":
                dept = requirements.get("dept")
                number = requirements.get("number")
                course_id = f"{dept} {number}"
                course = self._course_manager.by_id(course_id)
                return ReqCourse(course, self._degree_id)
            elif type.endswith("-range"):
                minimum = requirements.get("n")
                maximum = requirements.get("m")
                options = requirements.get("options")
                options = [parse_recursive_helper(option) for option in options]
                if type == "credit-range":
                    return CreditRange(minimum, maximum, options, required)
                elif type == "course-range":
                    return CourseRange(minimum, maximum, options, required)
                else:
                    raise ValueError(f"Found invalid degree requirement type {type}.")
            elif type == "true":
                return ReqTrue()
            elif type == "all":
                req = requirements.get("req")
                req = [parse_recursive_helper(option) for option in req]
                return All(req)
            elif type == "false":
                return ReqFalse()
            else:
                raise ValueError(f"Found invalid degree requirement type {type}.")

        if len(requirements) == 0:
            raise ValueError("Trying to parse non-existant requirements")

        return parse_recursive_helper(requirements, True)

    def generate(self) -> z3.BoolRef:
        return self._requirements.eval()
