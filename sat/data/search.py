import json
from pprint import pprint

courses = None

with open("all-ided-courses.json", "r") as infile:
    courses = json.load(infile)

for course in courses:
    coreqs = course["coreq"]
    if coreqs["type"] != "true":
        print()
        print(course["id"])
        for c in course["coreq"]:
            if c not in course["preorco"]:
                print("WINNER")
                print("prereq", end=" ")
                pprint(course["prereq"])
                print("preorco", end=" ")
                pprint(course["preorco"])
                print("coreq", end=" ")
                pprint(course["coreq"])
