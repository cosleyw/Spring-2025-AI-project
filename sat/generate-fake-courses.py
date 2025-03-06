from random import randint, choice
from faker import Faker
from typing import Any
import json

fake = Faker()

count = 100
file_name = "courses.json"
seasons = [
    "FALL",
    "SPRING",
    "FALL_AND_SPRING",
    "VARIES",
    "EVEN_FALL",
    "ODD_FALL",
    "EVEN_SPRING",
    "ODD_SPRING",
]

courses = []


def generate_requirements(limit: int) -> dict[Any, Any]:
    v = randint(0, 100)
    if v < 40:
        return {
            "type": "PRE",
            "value": randint(1, limit),
        }
    elif v < 80:
        return {
            "type": "CO",
            "value": randint(1, limit),
        }
    elif v < 90:
        return {
            "type": "RANK",
            "value": choice(["JR", "SR"]),
        }
    else:
        x = randint(1, 2)
        if x == 1:
            return {
                "type": "AND",
                "items": [generate_requirements(limit) for _ in range(randint(2, 5))],
            }
        else:
            return {
                "type": "OR",
                "items": [generate_requirements(limit) for _ in range(randint(2, 5))],
            }


for i in range(count):
    item = {
        "name": fake.unique.company(),
        "id": i + 1,
        "credits": randint(2, 5),
        "season": choice(seasons),
    }
    if randint(1, 10) > 4:
        item["requirements"] = generate_requirements(i + 1)

    courses.append(item)

with open(file_name, "w") as f:
    json.dump({"courses": courses}, f)
