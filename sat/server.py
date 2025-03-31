from typing import Annotated
from fastapi import Depends, FastAPI, Query
from models import ScheduleConfiguration

from main import Course, CourseSATSolver, Degree

app = FastAPI(
    title="Schedule Generator API",
    description="This is a basic API for generaing course schedules.",
    version="0.0.1",
    openapi_tags=[
        # {"name": "items", "description": "Operations with items."},
    ],
)


def parseCourseIds(desired_course_ids: str) -> list[str]:
    """Comma seperates list of course ids"""
    return desired_course_ids.split(",")


@app.post("/schedules/generate")
async def generate_schedule(configuration: Annotated[ScheduleConfiguration, Query()]):
    Course.courses = {}
    Degree.degrees = {}

    c: CourseSATSolver = CourseSATSolver(
        semester_count=configuration.semester_count,
        min_credit_per_semester=configuration.min_credit_per_semester,
        max_credits_per_semester=configuration.max_credit_per_semester,
        first_semester_sophomore=configuration.first_semester_sophomore,
        first_semester_junior=configuration.first_semester_junior,
        first_semester_senior=configuration.first_semester_senior,
        first_semester_graduate=configuration.first_semester_graduate,
        first_semester_doctoral=configuration.first_semester_doctoral,
        starts_as_fall=configuration.starts_as_fall,
        start_year=configuration.start_year,
        desired_course_ids=configuration.desired_course_ids,
        undesired_course_ids=configuration.undesired_course_ids,
        desired_degree_ids=configuration.desired_degree_ids,
    )

    c.setup()
    c.add_degree_reqs()
    c.minimize()
    c.solve()
    c.display()
    print(configuration)
    return {
        "status": "success",
        "schedule": c.get_plan_with_ids(),
    }
