import json, pathlib  # noqa: E401

REPLIES = json.load(open(pathlib.Path.cwd().joinpath("src/ui/replies.json")))
