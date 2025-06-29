import json
from pathlib import Path

import yaml


def compare_json_files(f1, f2):
    """Compare two JSON files by content."""
    with Path(f1).open() as a, Path(f2).open() as b:
        return json.load(a) == json.load(b)


def compare_yaml_files(f1, f2):
    """Compare two YAML files by loading them as objects."""
    with Path(f1).open() as a, Path(f2).open() as b:
        return yaml.safe_load(a) == yaml.safe_load(b)
