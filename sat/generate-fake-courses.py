from random import randint, choice
from faker import Faker
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


def randint_but_exclude(lower, upper, exclude):
    return randint(lower, exclude)
    # if lower == upper and lower == exclude:
    #    raise ValueError("Doesn't work like that")

    # while True:
    #    r = randint(lower, upper)
    #    if r < exclude:
    #        return r


def generate_requirements(exclude):
    v = randint(0, 100)
    if v < 40:
        return {
            "type": "PRE",
            "value": randint_but_exclude(1, count, exclude),
        }
    elif v < 80:
        return {
            "type": "CO",
            "value": randint_but_exclude(1, count, exclude),
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
                "items": [generate_requirements(exclude) for _ in range(randint(2, 5))],
            }
        else:
            return {
                "type": "OR",
                "items": [generate_requirements(exclude) for _ in range(randint(2, 5))],
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
