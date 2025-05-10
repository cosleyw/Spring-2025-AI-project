from pydantic import BaseModel, Field, computed_field


def parse_course_ids(course_ids_str: str | None) -> list[tuple[str] | tuple[str, int]]:
    if course_ids_str is None:
        return []

    course_str_list: list[str] = course_ids_str.split(",")
    raw_course_id_list: list[list[str]] = [course.split("@") for course in course_str_list]
    course_tuple_list: list[tuple[str] | tuple[str, int]] = []
    # Code more complicated than I would like to ensure the types are correct
    for raw_course_id in raw_course_id_list:
        if len(raw_course_id) == 2:
            course_id = (raw_course_id[0], int(raw_course_id[1]))
        elif len(raw_course_id) == 1:
            course_id = (raw_course_id[0],)
        else:
            raise ValueError("Expected course tuples to only be length 1 or 2")
        course_tuple_list.append(course_id)

    return course_tuple_list


def parse_transferred_course_ids(coures_ids_str: str | None) -> list[str]:
    if coures_ids_str is None:
        return []

    return coures_ids_str.split(",")


def parse_degree_ids(degree_id_str: str) -> list[str]:
    return degree_id_str.split(";")


class ScheduleConfiguration(BaseModel):
    semester_count: int = Field(4, description="Number of semester to generate a schedule for")
    min_credit_per_semester: int = Field(0, description="Minimum credits allowed at a given semester (inclusive)")
    max_credit_per_semester: int = Field(16, description="Maximum credits allowed at a given semester (inclusive)")
    starts_as_fall: bool = Field(True, description="Whether the first semester is a Fall")
    start_year: int = Field(2025, description="The first year the schedule should generate for")
    transferred_course_ids_str: str | None = Field(None, description="A list of course ids for transferred in courses")
    desired_course_ids_str: str | None = Field(None, description="A list of course ids (optional affixed with @<semester>) that should be included in the schedule")
    undesired_course_ids_str: str | None = Field(None, description="A list of course ids (optional affixed with @<semester>) that should not be included in the schedule")
    desired_degree_ids_str: str = Field(description="A list of degree ids that should be followed")
    first_semester_sophomore: int | None = Field(
        None,
        description="A (one indexed) number representing the first semester when a sophomore or empty is never reaching that rank",
        ge=1,
    )
    first_semester_junior: int | None = Field(
        None,
        description="A (one indexed) number representing the first semester when a junior or empty is never reaching that rank. Must be less or equal to number of semesters.",
        ge=1,
    )
    first_semester_senior: int | None = Field(
        None,
        description="A (one indexed) number representing the first semester when a senior or empty is never reaching that rank. Must be less than or equal to number of semesters.",
        ge=1,
    )

    @computed_field
    @property
    def desired_course_ids(self) -> list[tuple[str] | tuple[str, int]]:
        return parse_course_ids(self.desired_course_ids_str)

    @computed_field
    @property
    def undesired_course_ids(self) -> list[tuple[str] | tuple[str, int]]:
        return parse_course_ids(self.undesired_course_ids_str)

    @computed_field
    @property
    def desired_degree_ids(self) -> list[str]:
        return parse_degree_ids(self.desired_degree_ids_str)

    @computed_field
    @property
    def transferred_course_ids(self) -> list[str]:
        return parse_transferred_course_ids(self.transferred_course_ids_str)
