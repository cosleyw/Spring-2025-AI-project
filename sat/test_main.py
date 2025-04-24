from typing import Any, override
import unittest
import os

from main import CourseSATSolver


class TestCourseSATSolver(unittest.TestCase):
    def create_with_defaults(self, **kwargs) -> CourseSATSolver:
        return CourseSATSolver(
            **{
                **{
                    **self.default_args,
                    **kwargs,
                }
            }
        )

    def solve(self, c: CourseSATSolver) -> tuple[list[Any], list[Any]]:
        c.setup()
        c.add_degree_reqs()
        c.minimize()
        c.solve()
        plan = c.get_plan_with_ids()
        flat_plan = [course for sem in plan for course in sem]
        return plan, flat_plan

    @override
    def setUp(self) -> None:
        self.default_args = {
            "semester_count": 4,
            "min_credit_per_semester": 0,
            "max_credits_per_semester": 12,
            "first_semester_sophomore": 1,
            "first_semester_junior": 1,
            "first_semester_senior": 1,
            "starts_as_fall": True,
            "start_year": 2025,
            "transferred_course_ids": [],
            "desired_course_ids": [],
            "undesired_course_ids": [],
            "desired_degree_ids": ["CS:BA"],
        }

    def test_prereq(self):
        c: CourseSATSolver = self.create_with_defaults(
            semester_count=2,
            desired_degree_ids=["cs 2100"],
            courses_file_name=os.path.join("data", "cs-2100-pre.json"),
            degrees_file_name=os.path.join("data", "single-course-degree.json"),
        )

        c.setup()
        c.add_degree_reqs()
        c.solve_all()
        plans = c.get_plans_with_ids()

        self.assertEqual(len(plans), 1)

        self.assertEqual(
            plans[0],
            [[], ["cs 1100"], ["cs 2100"]],
        )

    def test_coreq(self):
        c: CourseSATSolver = self.create_with_defaults(
            semester_count=2,
            desired_degree_ids=["cs 2100"],
            courses_file_name=os.path.join("data", "cs-2100-co.json"),
            degrees_file_name=os.path.join("data", "single-course-degree.json"),
        )

        c.setup()
        c.add_degree_reqs()
        c.solve_all()
        plans = c.get_plans_with_ids()

        self.assertEqual(len(plans), 1)

        self.assertTrue("cs 1100" in plans[0][1])
        self.assertTrue("cs 2100" in plans[0][1])
        self.assertTrue(len([course for sem in plans[0] for course in sem]), 2)

    def test_preorcoreq(self):
        c: CourseSATSolver = self.create_with_defaults(
            semester_count=2,
            desired_degree_ids=["cs 2100"],
            courses_file_name=os.path.join("data", "cs-2100-preorco.json"),
            degrees_file_name=os.path.join("data", "single-course-degree.json"),
        )

        c.setup()
        c.add_degree_reqs()
        c.solve_all()
        plans = c.get_plans_with_ids()

        self.assertEqual(len(plans), 2)

        self.assertEqual(
            sorted(plans),
            sorted(
                [
                    [[], ["cs 1100"], ["cs 2100"]],
                    [[], ["cs 2100", "cs 1100"], []],
                ]
            ),
        )

    def test_flat_credit_range(self):
        c: CourseSATSolver = self.create_with_defaults(
            semester_count=4,
            courses_file_name=os.path.join("data", "cs-courses.json"),
            degrees_file_name=os.path.join("data", "flat-degree-credits.json"),
        )

        _, flat_plan = self.solve(c)

        self.assertEqual(
            len(flat_plan),
            4,
        )

    def test_flat_course_range(self):
        c: CourseSATSolver = self.create_with_defaults(
            semester_count=4,
            courses_file_name=os.path.join("data", "cs-courses.json"),
            degrees_file_name=os.path.join("data", "flat-degree-courses.json"),
        )

        c.setup()
        c.add_degree_reqs()
        c.minimize()
        c.solve()
        plan = c.get_plan_with_ids()
        flat_plan = [course for sem in plan for course in sem]

        print(plan)

        self.assertEqual(
            sorted(flat_plan),
            sorted(["cs 1410", "cs 1510", "cs 1800"]),
        )

    def test_split_course_range(self):
        c: CourseSATSolver = self.create_with_defaults(
            semester_count=2,
            courses_file_name=os.path.join("data", "cs-courses-noreqs.json"),
            degrees_file_name=os.path.join("data", "split-degree-courses.json"),
        )

        c.setup()
        c.add_degree_reqs()
        c.minimize()
        self.assertTrue(c.solve())
        plan = c.get_plan_with_ids()
        flat_plan = [course for sem in plan for course in sem]

        self.assertEqual(
            sorted(flat_plan),
            sorted(["cs 1410"]),
        )

    def test_simple_layered_credits(self):
        c = self.create_with_defaults(
            courses_file_name=os.path.join("data", "cs-courses.json"),
            degrees_file_name=os.path.join("data", "simple-cs-degree-credits.json"),
        )

        c.setup()
        c.add_degree_reqs()
        c.minimize()
        c.solve()
        plan = c.get_plan_with_ids()
        flat_plan = [course for sem in plan for course in sem]

        self.assertEqual(
            sorted(flat_plan),
            sorted(["cs 1410", "cs 1510", "cs 1800"]),
        )

    def test_simple_layered(self):
        c = self.create_with_defaults(
            courses_file_name=os.path.join("data", "cs-courses.json"),
            degrees_file_name=os.path.join("data", "simple-layered-degree.json"),
        )

        c.setup()
        c.add_degree_reqs()
        c.minimize()
        c.solve()
        plan = c.get_plan_with_ids()
        flat_plan = [course for sem in plan for course in sem]

        self.assertEqual(
            len(flat_plan),
            1,
        )

    def test_simple_layered_02(self):
        c: CourseSATSolver = self.create_with_defaults(
            courses_file_name=os.path.join("data", "cs-courses.json"),
            degrees_file_name=os.path.join("data", "simple-layered-degree-02.json"),
        )

        c.setup()
        c.add_degree_reqs()
        c.minimize()
        c.solve()
        plan = c.get_plan_with_ids()
        flat_plan = [course for sem in plan for course in sem]

        first_group_count = flat_plan.count("cs 1410") + flat_plan.count("cs 1510") + flat_plan.count("cs 1520")
        second_group_count = flat_plan.count("cs 1800") + flat_plan.count("cs 2530") + flat_plan.count("cs 3730") + flat_plan.count("cs 5730")

        self.assertLessEqual(first_group_count, 2)
        self.assertLessEqual(second_group_count, 2)

        self.assertEqual(
            len(flat_plan),
            4,
        )

    def test_simple_layered_03(self):
        c: CourseSATSolver = self.create_with_defaults(
            courses_file_name=os.path.join("data", "cs-courses-noreqs.json"),
            degrees_file_name=os.path.join("data", "simple-layered-degree-03.json"),
        )

        c.setup()
        c.add_degree_reqs()
        c.minimize()
        c.solve()
        plan = c.get_plan_with_ids()
        flat_plan = [course for sem in plan for course in sem]

        # first_group_count = flat_plan.count("cs 1410") + flat_plan.count("cs 1510") + flat_plan.count("cs 1520")
        # second_group_count = flat_plan.count("cs 1800") + flat_plan.count("cs 2530") + flat_plan.count("cs 3730") + flat_plan.count("cs 5730")

        self.assertEqual(
            len(flat_plan),
            3,
        )

    def test_simple_layered_04(self):
        c: CourseSATSolver = self.create_with_defaults(
            semester_count=8,
            courses_file_name=os.path.join("data", "cs-courses.json"),
            degrees_file_name=os.path.join("data", "simple-layered-degree-04.json"),
        )

        c.setup()
        c.add_degree_reqs()
        c.minimize()
        self.assertTrue(c.solve())

        print(c.get_plan_with_ids())


"""
    def test_disjoint_degree(self):
        c: CourseSATSolver = CourseSATSolver(
            semester_count=2,
            min_credit_per_semester=0,
            max_credits_per_semester=4,
            first_semester_sophomore=1,
            first_semester_junior=1,
            first_semester_senior=1,
            starts_as_fall=True,
            start_year=2025,
            transferred_course_ids=[],
            desired_course_ids=[],
            undesired_course_ids=[],
            desired_degree_ids=["CS:BA"],
            courses_file_name=os.path.join("data", "legacy", "disjoint-cs-courses.json"),
            degrees_file_name=os.path.join("data", "legacy", "disjoint-cs-degree.json"),
        )

        c.setup()
        c.add_degree_reqs()
        c.minimize()
        while c.solve():
            pass

        plan_ids = []
        for plan in c.possible_plans:
            semester_ids = []
            for semester in plan:
                courses = [c.get_id() for c in semester]
                semester_ids.append(courses)
            plan_ids.append(semester_ids)

        self.assertEqual(
            sorted(plan_ids),
            sorted([[[], ["CS1130"], ["CS1000"]], [[], ["CS1000"], ["CS1130"]], [[], ["CS1000"], ["CS1510"]], [[], ["CS1130"], ["CS1510"]], [[], ["CS1510"], ["CS1130"]], [[], ["CS1510"], ["CS1000"]]]),
        )
        """
