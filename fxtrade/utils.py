import json
import gzip
from pathlib import Path


def save_as_json_gzip(data: list, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with gzip.open(path, "wb") as f:
        f.write(json.dumps(data).encode("utf_8"))

    return path


def load_json_gzip(path: Path):
    with gzip.open(path, "rb") as f:
        data = f.read()

    return json.loads(data.decode("utf-8"))
