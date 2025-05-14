import json

courses = None

with open("courses.json", "r") as infile:
    courses = json.load(infile)

i = 0
while i < len(courses):
    course = courses[i]
    if course["dept"] != "cs":
        print("Deleting", course)
        del courses[i]
        continue
    i += 1


with open("cs-courses.json", "w") as outfile:
    json.dump(courses, outfile)
