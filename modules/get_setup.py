import json


def get_setup():
    setup = {}
    with open("setup.json", "r") as f:
        setup = json.loads(f.read())
        f.close()

    return setup
