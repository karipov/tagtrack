import json, pathlib  # noqa: E401

CONFIG = json.load(open(pathlib.Path.cwd().joinpath("src/config/config.json")))
