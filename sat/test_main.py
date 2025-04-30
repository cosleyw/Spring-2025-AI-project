from typing import Any, override
import unittest
import os
import logging

from main import CourseSATSolver

TEST_DATA_DIR = os.path.join("data", "test")

# Here is the proposed layout/structure of my tests

## Course Focused
### X pre req
### X co req
### X pre or co req
### X non-repetition
#### X special non-repetition across a single degree?/item cannot count for multiple areas in a single section
### ~n-credit repetition (not implemented currently)~
### ~credit range (not implemented currently)~
### X seasons
### X seasons when changing start year/spring
### X some req
### X all req
### X nested some/all? do those exist?
### X invalid in some is possible
### X invalid in all is impossible

## Degree Focused
### X course range
### X credit range
### X layered course range
### X layered credit range
### X nested mix of both?
### ~major (not implemented currently)~
### 2 distinct degrees
### 2 degrees with overlap of course
#### where that course is unused
#### where that course is used
### true value
### false value
### all
### invalid courses are ignored
### check semester upper/lower bounds


def test_path(file_name):
    return os.path.join(TEST_DATA_DIR, file_name)


class TestCourseSATSolver(unittest.TestCase):
    def create_with_defaults(self, **kwargs) -> CourseSATSolver:
        c: CourseSATSolver = CourseSATSolver.from_values(
            **{
                **self.default_args,
                **kwargs,
            }
        )
        c.setup()
        return c

    def solve(self, c: CourseSATSolver) -> tuple[list[Any], list[Any]]:
        c.solve()
        plan = c.get_plan_with_ids()
        flat_plan = self.flatten(plan)
        return plan, flat_plan

    def flatten(self, plan):
        return [course for sem in plan for course in sem]

    def index_of(self, course, plan):
        for i, semester in enumerate(plan):
            if course in semester:
                return i
        return -1

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

    def test_noreq(self):
        c: CourseSATSolver = self.create_with_defaults(
            desired_degree_ids=["cs 2100"],
            courses_file_name=test_path("noreq-cs2100.json"),
            degrees_file_name=test_path("single-course-degree.json"),
        )

        c.solve_all()
        plans = c.get_plans_with_ids()

        self.assertEqual(len(plans), 4, "Number of schedules for degree with 1 course and no reqs")

        for plan in plans:
            flat = self.flatten(plan)
            self.assertListEqual(flat, ["cs 2100"], "Correct courses in schedule for 1 course degree with no reqs")

    def test_prereq(self):
        c: CourseSATSolver = self.create_with_defaults(
            desired_degree_ids=["cs 2100"],
            courses_file_name=test_path("prereq-cs2100.json"),
            degrees_file_name=test_path("single-course-degree.json"),
        )

        c.solve_all()
        plans = c.get_plans_with_ids()

        self.assertEqual(len(plans), 6, "Number of schedules for degree with 1 course and a prereq")

        for plan in plans:
            flat = self.flatten(plan)
            self.assertEqual(len(flat), 2, "Taking required 2 courses for degree+prereq")
            self.assertEqual(set(flat), set(["cs 1100", "cs 2100"]))
            req_taken_sem = self.index_of("cs 1100", plan)
            main_taken_sem = self.index_of("cs 2100", plan)
            self.assertLess(req_taken_sem, main_taken_sem, "Pre taken before main course")

    def test_coreq(self):
        c: CourseSATSolver = self.create_with_defaults(
            desired_degree_ids=["cs 2100"],
            courses_file_name=test_path("coreq-cs2100.json"),
            degrees_file_name=test_path("single-course-degree.json"),
        )

        c.solve_all()
        plans = c.get_plans_with_ids()

        self.assertEqual(len(plans), 4, "Number of schedules for degree with 1 course and a coreq")

        for plan in plans:
            flat = self.flatten(plan)
            self.assertEqual(len(flat), 2, "Taking required 2 courses for degree+coreq")
            self.assertEqual(set(flat), set(["cs 1100", "cs 2100"]), "Taking correct 2 courses for degree+coreq")
            req_taken_sem = self.index_of("cs 1100", plan)
            main_taken_sem = self.index_of("cs 2100", plan)
            self.assertEqual(req_taken_sem, main_taken_sem, "Co taken same semester as main course")

    def test_preorcoreq(self):
        c: CourseSATSolver = self.create_with_defaults(
            desired_degree_ids=["cs 2100"],
            courses_file_name=test_path("preorco-cs2100.json"),
            degrees_file_name=test_path("single-course-degree.json"),
        )

        c.solve_all()
        plans = c.get_plans_with_ids()

        c.display()

        self.assertEqual(len(plans), 10)

        for plan in plans:
            flat = self.flatten(plan)
            self.assertEqual(len(flat), 2, "Taking required 2 courses for degree with pre/co req")
            self.assertEqual(set(flat), set(["cs 1100", "cs 2100"]), "Taking required courses for degree+pre/co")
            req_taken_sem = self.index_of("cs 1100", plan)
            main_taken_sem = self.index_of("cs 2100", plan)
            self.assertLessEqual(req_taken_sem, main_taken_sem, "Pre/co taken semester has to be before or equal to main taken semester")

    def test_invalid(self):
        c: CourseSATSolver = self.create_with_defaults(
            desired_degree_ids=["cs 2100"],
            courses_file_name=test_path("invalid-cs2100.json"),
            degrees_file_name=test_path("single-course-degree.json"),
        )

        self.assertFalse(c.solve(), "Cannot take course with invalid req")

    def test_some(self):
        c: CourseSATSolver = self.create_with_defaults(
            desired_degree_ids=["cs 2100"],
            semester_count=2,
            courses_file_name=test_path("some-cs2100.json"),
            degrees_file_name=test_path("single-course-degree.json"),
        )

        c.minimize()
        plan, flat_plan = self.solve(c)

        self.assertEqual(len(flat_plan), 2, "Taking 2 course (main+some preq)")
        self.assertListEqual(plan[2], ["cs 2100"], "Main taken second semester after some preq")

    def test_invalid_some(self):
        c: CourseSATSolver = self.create_with_defaults(
            desired_degree_ids=["cs 2100"],
            semester_count=2,
            courses_file_name=test_path("invalid-some-cs2100.json"),
            degrees_file_name=test_path("single-course-degree.json"),
        )

        c.minimize()
        plan, flat_plan = self.solve(c)

        self.assertEqual(len(flat_plan), 2, "Taking 2 course (main+some preq); ignoring invalid node")
        self.assertListEqual(plan[2], ["cs 2100"], "Main taken second semester after some preq; ignoring invalid node")

    def test_nested_some(self):
        c: CourseSATSolver = self.create_with_defaults(
            desired_degree_ids=["cs 2100"],
            semester_count=2,
            courses_file_name=test_path("some-nested-cs2100.json"),
            degrees_file_name=test_path("single-course-degree.json"),
        )

        c.minimize()
        plan, flat_plan = self.solve(c)

        self.assertEqual(len(flat_plan), 2, "Taking 2 course (main+some preq)")
        self.assertListEqual(plan[2], ["cs 2100"], "Main taken second semester after some preq")

    def test_all(self):
        c: CourseSATSolver = self.create_with_defaults(
            desired_degree_ids=["cs 2100"],
            semester_count=2,
            courses_file_name=test_path("all-cs2100.json"),
            degrees_file_name=test_path("single-course-degree.json"),
        )

        c.minimize()
        plan, flat_plan = self.solve(c)

        self.assertEqual(len(flat_plan), 4, "Taking 4 course (main+all preq)")
        self.assertEqual(set(plan[1]), set(["cs 1100", "cs 1000", "cs 1025"]), "All preqs taken first semester")
        self.assertListEqual(plan[2], ["cs 2100"], "Main taken second semester after all preq")

    def test_invalid_all(self):
        c: CourseSATSolver = self.create_with_defaults(
            desired_degree_ids=["cs 2100"],
            semester_count=2,
            courses_file_name=test_path("invalid-all-cs2100.json"),
            degrees_file_name=test_path("single-course-degree.json"),
        )

        c.minimize()
        self.assertFalse(c.solve(), "Cannot solve all with invalid node")

    def test_nested_all(self):
        c: CourseSATSolver = self.create_with_defaults(
            desired_degree_ids=["cs 2100"],
            semester_count=2,
            courses_file_name=test_path("all-nested-cs2100.json"),
            degrees_file_name=test_path("single-course-degree.json"),
        )

        c.minimize()
        plan, flat_plan = self.solve(c)

        self.assertEqual(len(flat_plan), 4, "Taking 4 course (main+all preq)")
        self.assertEqual(set(plan[1]), set(["cs 1100", "cs 1000", "cs 1025"]), "All preqs taken first semester")
        self.assertListEqual(plan[2], ["cs 2100"], "Main taken second semester after all preq")

    def test_nested_mixed(self):
        c: CourseSATSolver = self.create_with_defaults(
            desired_degree_ids=["cs 2100"],
            semester_count=2,
            courses_file_name=test_path("mixed-nested-cs2100.json"),
            degrees_file_name=test_path("single-course-degree.json"),
        )

        c.minimize()
        plan, flat_plan = self.solve(c)

        self.assertEqual(len(flat_plan), 4, "Taking 4 course (main+all/some preq)")

        taken_all_reqs = True
        if ("cs 1100" not in plan[1]) or ("cs 1170" not in plan[1]) or (("cs 1000" not in plan[1]) and ("cs 1025" not in plan[1])):
            taken_all_reqs = False
        self.assertTrue(taken_all_reqs, "Taken all 3 nested mixed requirements")

        self.assertListEqual(plan[2], ["cs 2100"], "Main taken second semester after all preq")

    def test_non_repetition(self):
        c: CourseSATSolver = self.create_with_defaults(
            min_credit_per_semester=3,
            semester_count=2,
            desired_degree_ids=["cs 2100"],
            courses_file_name=test_path("noreq-cs2100.json"),
            degrees_file_name=test_path("single-course-degree.json"),
        )

        self.assertFalse(c.solve(), "Impossible degree due to course repetition")

    def test_non_repetition_within_degree(self):
        c: CourseSATSolver = self.create_with_defaults(
            desired_degree_ids=["cs 2100"],
            courses_file_name=test_path("noreq-cs2100.json"),
            degrees_file_name=test_path("course-rep-degree.json"),
        )

        self.assertFalse(c.solve(), "Course cannot count for multiple sections in a degree")

    def test_start_seasons(self):
        def start_at(start_fall, start_year, season_name):
            return self.create_with_defaults(
                starts_as_fall=start_fall,
                start_year=start_year,
                semester_count=4,
                desired_degree_ids=["cs 2100"],
                courses_file_name=test_path(os.path.join("season", f"{season_name}-cs2100.json")),
                degrees_file_name=test_path("single-course-degree.json"),
            )

        def validate(start_fall, start_year, season_name, valid_locations):
            c: CourseSATSolver = start_at(start_fall, start_year, season_name)
            c.solve_all()
            self.assertEqual(len(c.get_plans_with_ids()), len(valid_locations), "Correct number of schedules with custom season")
            c.display()
            for plan in c.get_plans_with_ids():
                taken_during_valid_season = False
                for sem in valid_locations:
                    if len(plan[sem + 1]) > 0:
                        taken_during_valid_season = True
                self.assertTrue(taken_during_valid_season, "Course taken during a valid custom season")

        start_fall = True
        start_year = 2025
        validate(start_fall, start_year, "fall", [0, 2])
        validate(start_fall, start_year, "odd-falls", [0])
        validate(start_fall, start_year, "spring-and-even-falls", [1, 2, 3])
        validate(start_fall, start_year, "even-falls", [2])
        validate(start_fall, start_year, "spring-and-summer", [1, 3])
        validate(start_fall, start_year, "odd-springs", [3])
        validate(start_fall, start_year, "even-springs", [1])
        validate(start_fall, start_year, "fall-spring-summer", [0, 1, 2, 3])
        validate(start_fall, start_year, "summer", [])

        start_fall = False
        start_year = 2025
        validate(start_fall, start_year, "fall", [1, 3])
        validate(start_fall, start_year, "odd-falls", [1])
        validate(start_fall, start_year, "even-falls", [3])
        validate(start_fall, start_year, "spring-and-even-falls", [0, 2, 3])
        validate(start_fall, start_year, "spring-and-summer", [0, 2])
        validate(start_fall, start_year, "odd-springs", [0])
        validate(start_fall, start_year, "even-springs", [2])
        validate(start_fall, start_year, "fall-spring-summer", [0, 1, 2, 3])
        validate(start_fall, start_year, "summer", [])

        start_fall = True
        start_year = 2026
        validate(start_fall, start_year, "fall", [0, 2])
        validate(start_fall, start_year, "odd-falls", [2])
        validate(start_fall, start_year, "even-falls", [0])
        validate(start_fall, start_year, "spring-and-even-falls", [0, 1, 3])
        validate(start_fall, start_year, "spring-and-summer", [1, 3])
        validate(start_fall, start_year, "odd-springs", [1])
        validate(start_fall, start_year, "even-springs", [3])
        validate(start_fall, start_year, "fall-spring-summer", [0, 1, 2, 3])
        validate(start_fall, start_year, "summer", [])

        start_fall = False
        start_year = 2026
        validate(start_fall, start_year, "fall", [1, 3])
        validate(start_fall, start_year, "odd-falls", [3])
        validate(start_fall, start_year, "even-falls", [1])
        validate(start_fall, start_year, "spring-and-even-falls", [0, 1, 2])
        validate(start_fall, start_year, "spring-and-summer", [0, 2])
        validate(start_fall, start_year, "odd-springs", [2])
        validate(start_fall, start_year, "even-springs", [0])
        validate(start_fall, start_year, "fall-spring-summer", [0, 1, 2, 3])
        validate(start_fall, start_year, "summer", [])

    def test_flat_credit_range(self):
        c: CourseSATSolver = self.create_with_defaults(
            desired_degree_ids=["CS:BA"],
            courses_file_name=test_path("cs-courses.json"),
            degrees_file_name=test_path("flat-degree-credits.json"),
        )

        c.minimize()
        _, flat_plan = self.solve(c)
        c.display()

        self.assertEqual(
            len(flat_plan),
            4,
            "Contains minimum number of courses within credit range",
        )

    def test_flat_course_range(self):
        c: CourseSATSolver = self.create_with_defaults(
            desired_degree_ids=["CS:BA"],
            courses_file_name=test_path("cs-courses.json"),
            degrees_file_name=test_path("flat-degree-courses.json"),
        )

        c.minimize()
        _, flat_plan = self.solve(c)

        self.assertEqual(
            len(flat_plan),
            3,
            "Contains minimum number of courses within course range",
        )

    def test_split_course_range(self):
        c: CourseSATSolver = self.create_with_defaults(
            semester_count=2,
            courses_file_name=test_path("cs-courses-noreqs.json"),
            degrees_file_name=test_path("split-degree-courses.json"),
        )

        c.minimize()
        self.assertTrue(c.solve())
        plan = c.get_plan_with_ids()
        flat_plan = [course for sem in plan for course in sem]

        self.assertEqual(
            sorted(flat_plan),
            sorted(["cs 1410"]),
            "Correct courses ignoring non-essential element",
        )

    def test_simple_layered_courses(self):
        c = self.create_with_defaults(
            courses_file_name=test_path("cs-courses.json"),
            degrees_file_name=test_path("simple-layered-courses.json"),
        )

        c.minimize()
        _, flat_plan = self.solve(c)

        self.assertEqual(len(flat_plan), 1, "Taking minimum number in layered credit range")

    def test_simple_layered_credits(self):
        c = self.create_with_defaults(
            courses_file_name=test_path("cs-courses.json"),
            degrees_file_name=test_path("simple-layered-credits.json"),
        )

        c.minimize()
        _, flat_plan = self.solve(c)

        self.assertEqual(
            len(flat_plan),
            3,
            "Taking minimum number in layered credit range",
        )

        self.assertEqual(
            set(flat_plan),
            set(["cs 1410", "cs 1510", "cs 1800"]),
            "Taking correct set of courses to meet layered requirements",
        )

    def test_layered(self):
        c = self.create_with_defaults(
            courses_file_name=test_path("cs-courses.json"),
            degrees_file_name=test_path("layered-degree-01.json"),
        )

        c.minimize()
        plan, flat_plan = self.solve(c)

        self.assertEqual(
            len(flat_plan),
            1,
        )

        self.assertIn(
            flat_plan[0],
            ["cs 1510", "cs 3730"],
            "Taking valid course to meet all reqs",
        )

    def test_layered_02(self):
        c: CourseSATSolver = self.create_with_defaults(
            courses_file_name=test_path("cs-courses.json"),
            degrees_file_name=test_path("layered-degree-02.json"),
        )

        c.minimize()
        _, flat_plan = self.solve(c)

        first_group_count = flat_plan.count("cs 1410") + flat_plan.count("cs 1510") + flat_plan.count("cs 1520")
        second_group_count = flat_plan.count("cs 1800") + flat_plan.count("cs 2530") + flat_plan.count("cs 3730") + flat_plan.count("cs 5730")

        self.assertLessEqual(first_group_count, 2, "Taking too many courses from first group")
        self.assertLessEqual(second_group_count, 2, "Taking too many courses from second group")

        self.assertEqual(len(flat_plan), 4, "Not taking enough overall courses for meta group")

    def test_layered_03(self):
        c: CourseSATSolver = self.create_with_defaults(
            courses_file_name=test_path("cs-courses-noreqs.json"),
            degrees_file_name=test_path("layered-degree-03.json"),
        )

        c.minimize()
        _, flat_plan = self.solve(c)

        self.assertEqual(len(flat_plan), 3, "Correct number of overall courses")

    def test_layered_04(self):
        c: CourseSATSolver = self.create_with_defaults(
            semester_count=8,
            courses_file_name=test_path("cs-courses.json"),
            degrees_file_name=test_path("layered-degree-04.json"),
        )

        c.minimize()
        self.assertTrue(c.solve())

        logging.info(c.get_plan_with_ids())


if __name__ == "__main__":
    unittest.main()
