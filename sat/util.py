import json


def load_solvable_degrees(degree_file_name, unsolvable_degree_file_name=None):
    unsolvable_degrees = []
    if unsolvable_degree_file_name is not None:
        with open(unsolvable_degree_file_name, "r") as unsolvable_degree_file:
            unsolvable_degrees = json.load(unsolvable_degree_file)["degrees"]

    degrees = {}
    with open(degree_file_name, "r") as file:
        for id, degree in json.load(file).items():
            if id not in unsolvable_degrees:
                degrees[id.replace(chr(160), " ")] = degree
    return degrees


if __name__ == "__main__":
    print(load_solvable_degrees())
