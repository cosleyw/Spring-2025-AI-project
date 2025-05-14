import json
from pprint import pprint

courses = None

with open("courses.json", "r") as infile:
    courses = json.load(infile)

for course in courses:
    for req in ["prereq", "coreq", "preorco"]:
        type = course[req]["type"]
        if type == "some" or type == "all":
            # print(course)
            # print()
            # print(f"{course['dept']}{course['number']} {req}: {course[req]}")
            # print(course[req]["req"])
            # print()
            if course[req]["req"][0]["type"] != "course":
                print()
                print(f"{course['dept']}{course['number']} {req}: {course[req]}")
