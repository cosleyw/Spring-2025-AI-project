from enum import StrEnum
import json

from config import DEGREES_FILE_NAME

selected_degree_str = "MECHANICAL ENGINEERING TECHNOLOGY BS (2024-PRESENT) 35DBS"

degree = None

with open(DEGREES_FILE_NAME, "r") as file:
    raw_degrees = json.load(file)

    for name, requirements in raw_degrees.items():
        if selected_degree_str.lower() in name.lower():
            print(f"Selected {name}...")
            degree = requirements


class ReqType(StrEnum):
    CreditRange = "credit-range"
    CourseRange = "course-range"
    All = "all"
    Tag = "tag"
    Course = "course"
    ReqFalse = "false"


def tab(level):
    return "\t" * level


def pprint(degree, level=0):
    if isinstance(degree, list):
        for req in degree:
            pprint(req, level)
        return

    type = ReqType(degree.get("type"))

    match type:
        case ReqType.CreditRange:
            m = degree.get("m")
            n = degree.get("n")
            print(f"{tab(level)}Credit Range ({n}-{m})")
            pprint(degree.get("options"), level + 1)
        case ReqType.CourseRange:
            m = degree.get("m")
            n = degree.get("n")
            print(f"{tab(level)}Course Range ({n}-{m})")
            pprint(degree.get("options"), level + 1)
        case ReqType.All:
            print(f"{tab(level)}All")
            pprint(degree.get("req"), level + 1)
        case ReqType.Tag:
            info = degree.get("info")
            print(f"{tab(level)}{info}")
            pprint(degree.get("node"), level)
        case ReqType.ReqFalse:
            print(f"{tab(level)}FALSE")
        case ReqType.Course:
            dept = degree.get("dept")
            number = degree.get("number")
            print(f"{tab(level)}{dept} {number}")
        case _:
            print(f"WARNING: Unknown tag type '{type}' for {degree}")


pprint(degree)
