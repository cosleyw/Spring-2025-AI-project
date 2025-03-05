from typeguard import typechecked
from typing import Any, override
from abc import abstractmethod
import z3.z3 as z3
from uuid import UUID, uuid4


@typechecked
class DegreeRequirement:
    def __init__(self):
        self._id: UUID = uuid4()

    def get_id(self) -> UUID:
        return self._id

    @abstractmethod
    def eval(self, exclusions: list[Any] = [], id_counts: dict[UUID, int] = {}) -> z3.BoolRef:
        # TODO: Do the math based on additional and some recursive function to make
        # this whole thing actually evaluated correctly.
        pass

    @abstractmethod
    def get_courses(self) -> list[Any]:
        pass

    @abstractmethod
    def get_nodes(self) -> list["DegreeRequirement"]:
        pass


@typechecked
class Disjoint(DegreeRequirement):
    def __init__(self, base: DegreeRequirement, additional: DegreeRequirement):
        super().__init__()
        self._base = base
        self._additional = additional

    @override
    def eval(self, exclusions: list[Any] = [], id_counts: dict[UUID, int] = {}) -> z3.BoolRef:
        exclusions = self._additional.get_courses()

        nodes: list[DegreeRequirement] = self.get_nodes()
        atleastk_nodes: list[AtLeastK] = []
        for node in nodes:
            if isinstance(node, AtLeastK):
                atleastk_nodes.append(node)

        def eval_helper(nodes: list[AtLeastK], id_counts: dict[UUID, int]) -> z3.BoolRef:
            if len(nodes) == 0:
                return z3.And(self._base.eval(exclusions, id_counts))

            active_node: AtLeastK = nodes[0]

            options = []

            for i in range(active_node.get_k() + 1):  # 0 -> k inclusive
                print(f"Recursive {i}...")
                options.append(
                    eval_helper(
                        nodes[1:],
                        {
                            active_node.get_id(): i,
                            **id_counts,
                        },
                    )
                )

            return z3.Or(options)

        # TODO: This is not type safe
        return eval_helper(atleastk_nodes, {})

    @override
    def get_courses(self) -> list[Any]:
        return [*self._base.get_courses(), *self._additional.get_courses()]

    @override
    def get_nodes(self) -> list["DegreeRequirement"]:
        return [self, *self._base.get_nodes(), *self._additional.get_nodes()]


@typechecked
class AtLeastK(DegreeRequirement):
    def __init__(self, k: int, items: list[DegreeRequirement]):
        super().__init__()
        self._k = k
        self._items = items

        if len(self._items) < self._k:
            raise ValueError(f"Cannot require {self._k} be taken from (len={len(self._items)}) items '{self._items}'")

        if self._k <= 0:
            raise ValueError("Cannot use AtLeastK with k <= 0; receieved k='{self._k}'")

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
    def eval(self, exclusions: list[Any] = [], id_counts: dict[UUID, int] = {}) -> z3.BoolRef:
        # TODO: Implement the evaluation model or none of this works
        values = [item.eval(exclusions, id_counts) for item in self._items]
        k: int
        if self._id in id_counts:
            k = id_counts[self._id]
        else:
            k = self._k
        return sum(values) >= k

    def get_k(self) -> int:
        return self._k


@typechecked
class And(DegreeRequirement):
    def __init__(self, items: list[DegreeRequirement]):
        super().__init__()
        self._items: list[DegreeRequirement] = items

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
    def eval(self, exclusions: list[Any] = [], id_counts: dict[UUID, int] = {}) -> z3.BoolRef:
        return z3.And([item.eval(exclusions, id_counts) for item in self._items])


@typechecked
class ReqCourse(DegreeRequirement):
    def __init__(self, course):
        super().__init__()
        self._course = course

    @override
    def get_courses(self) -> list[Any]:
        return [self._course]

    @override
    def get_nodes(self) -> list[DegreeRequirement]:
        return [self]

    @override
    def eval(self, exclusions: list[Any] = [], id_counts: dict[UUID, int] = {}) -> z3.BoolRef:
        if self._course in exclusions:
            return z3.BoolVal(False)
        return self._course.at()


# TODO: Implement degree requirements
@typechecked
class DegreeRequirementManager:
    def __init__(
        self,
        requirements: dict[Any, Any],
    ):
        self._raw_requirements = requirements
        self._requirements: DegreeRequirement

    def setup(
        self,
        course,
        degree,
        sophomore,
        junior,
        senior,
        graduate,
        doctoral,
    ) -> None:
        self._requirements = self._parse_recursive(
            self._raw_requirements,
            course,
            degree,
            **{
                "sophomore": sophomore,
                "junior": junior,
                "senior": senior,
                "graduate": graduate,
                "doctoral": doctoral,
            },
        )

    # TODO: Delete this method, it was only here for testing
    def get_courses(self):
        return self._requirements.get_courses()

    def _parse_recursive(self, requirements: Any, course, degree, **kwargs) -> DegreeRequirement:
        if len(requirements) == 0:
            raise ValueError("Trying to parse non-existant requirements")

        recurse = lambda req: self._parse_recursive(req, course, degree, **kwargs)

        type = requirements.get("type")

        match type:
            case "AND":
                items = requirements.get("items")
                parsed_items = [recurse(req) for req in items]
                return And(parsed_items)
            case "COURSE":
                return ReqCourse(course.by_id(requirements.get("value")))
            # case "RANK":
            #     return ReqRank(kwargs["junior"])
            # case "OR":  # TODO: Or is actually ann ATLEASTK with K=1, implement it as such
            #    items = requirements.get("items")
            #    parsed_items = [self._parse_recursive(req) for req in items]
            #    return Or(parsed_items)
            # case "ATLEASTK_CREDITS":
            #    k = requirements.get("k")
            #    courses = [self._parse_recursive(req) for req in requirements.get("items")]
            #    return sum(courses) >= k
            case "ATLEASTK":
                k = requirements.get("k")
                items = [recurse(req) for req in requirements.get("items")]
                return AtLeastK(k, items)
            case "DISJOINT":
                base = requirements.get("base")
                base = recurse(base)
                additional = requirements.get("additional")
                additional = recurse(additional)
                return Disjoint(base, additional)
            # case "ATMOSTK_COURSES":
            #    k = requirements.get("k")
            #    courses = [self._parse_recursive(req) for req in requirements.get("items")]
            #    return sum(courses) <= k
            # case "EXACTLYK_COURSES":
            #    k = requirements.get("k")
            #    courses = [self._parse_recursive(req) for req in requirements.get("items")]
            #    return sum(courses) == k
            case _:
                raise ValueError("Found invalid degree requirement")

    def generate(self) -> z3.BoolRef:
        return self._requirements.eval()
