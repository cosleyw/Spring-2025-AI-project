import json
from pprint import pprint

courses = None

with open("degrees.json", "r") as infile:
    degrees = json.load(infile)

degree_names = list(degrees.keys())

with open("degree-names", "w") as outfile:
    outfile.write("\n".join(degree_names))
