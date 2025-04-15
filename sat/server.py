from typing import Annotated
from fastapi import Depends, FastAPI, Query
from models import ScheduleConfiguration
from config import COURSES_FILE_NAME, DEGREES_FILE_NAME
import math
import json


from main import Course, CourseSATSolver, Degree, Offering

app = FastAPI(
    title="Schedule Generator API",
    description="This is a basic API for generaing course schedules.",
    version="0.0.1",
    openapi_tags=[
        {"name": "courses", "description": "Operations with courses."},
        {"name": "degrees", "description": "Operations with degrees."},
        {"name": "schedules", "description": "Operations with schedules."},
    ],
)


def parseCourseIds(desired_course_ids: str) -> list[str]:
    """Comma seperates list of course ids"""
    return desired_course_ids.split(",")


def load_courses():
    with open(COURSES_FILE_NAME, "r") as file:
        return json.load(file)["courses"]


def filter_credit_range(courses, min, max):
    if min is None:
        min = -math.inf
    if max is None:
        max = math.inf
    for course in courses:
        print(min, course["credits"], max)
        print(type(min), type(course["credits"]), type(max))
        print(min <= course["credits"] <= max)
    return list(filter(lambda course: min <= course["credits"] <= max, courses))


def filter_name_or_id(objects, query):
    if query is None:
        return objects
    query = query.lower()
    return list(filter(lambda object: query in object["name"].lower() or query in object["id"].lower(), objects))


def filter_season(courses, season: Offering | None):
    if season is None:
        return courses
    return list(filter(lambda course: course["season"] == season, courses))


def load_degrees():
    with open(DEGREES_FILE_NAME, "r") as file:
        return json.load(file)["degrees"]


@app.get("/courses", summary="Search for courses", tags=["courses"])
async def get_courses(
    query: str | None = None,
    min: int | None = None,
    max: int | None = None,
    season: Offering | None = None,
):
    courses = load_courses()
    courses = filter_name_or_id(courses, query)
    courses = filter_credit_range(courses, min, max)
    courses = filter_season(courses, season)
    return {"status": "success", "courses": courses}


@app.get("/courses/{id}", summary="Get a specific course by its id", tags=["courses"])
async def get_courses(id):
    courses = load_courses()
    for course in courses:
        if course["id"] == id:
            return {"status": "success", "course": course}
    return {"status": "failure", "message": "Was unable to find a course with the specified id"}


@app.get("/degrees", summary="Search for degrees", tags=["degrees"])
async def get_degrees(
    query: str | None = None,
):
    degrees = load_degrees()
    degrees = filter_name_or_id(degrees, query)
    return {"status": "success", "degrees": degrees}


@app.get("/degrees/{id}", summary="Get a specific degree by its id", tags=["degrees"])
async def get_degrees(id):
    degrees = load_degrees()
    for degree in degrees:
        if degree["id"] == id:
            return {"status": "success", "degree": degree}
    return {"status": "failure", "message": "Was unable to find a degree with the specified id"}


@app.get("/schedules/generate", summary="Generate a user schedule", tags=["schedules"])
def generate_schedule(configuration: Annotated[ScheduleConfiguration, Query()]):
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
