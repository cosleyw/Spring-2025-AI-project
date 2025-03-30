import unittest
import os

from main import CourseSATSolver

# semester_count = 2  # Number of semester to calculate for
# min_credit_per_semester = 0  # Minimum credits (inclusive)
# max_credits_per_semester = 4  # Maximum credits (inclusive)
# starts_as_fall = True
# start_year = 2025
# transferred_course_ids: list[str] = []  # ["CS1410", "CS1510"]
# desired_course_ids: list[tuple[str] | tuple[str, int]] = [
#    # ("CS3430/5430", 4),
#    # ("CS1160",),
# ]
# undesired_course_ids: list[tuple[str] | tuple[str, int]] = [
#    # ("CS4410/5410",),
# ]
# desired_degree_ids: list[str] = ["CS:BA"]
## NOTE: One-indexed!
# first_semester_sophomore: int | None = 1
# first_semester_junior: int | None = 1
# first_semester_senior: int | None = 1
# first_semester_graduate: int | None = None
# first_semester_doctoral: int | None = None


class TestCourseSATSolver(unittest.TestCase):
    def test_disjoint_degree(self):
        c: CourseSATSolver = CourseSATSolver(
            semester_count=2,
            min_credit_per_semester=0,
            max_credits_per_semester=4,
            first_semester_sophomore=1,
            first_semester_junior=1,
            first_semester_senior=1,
            first_semester_graduate=None,
            first_semester_doctoral=None,
            starts_as_fall=True,
            start_year=2025,
            desired_course_ids=[],
            undesired_course_ids=[],
            desired_degree_ids=["CS:BA"],
            courses_file_name=os.path.join("data", "disjoint-cs-courses.json"),
            degrees_file_name=os.path.join("data", "disjoint-cs-degree.json"),
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
