import sys
from collections.abc import Mapping
from pathlib import Path

import yaml


def load_yaml(file_path):
    with Path(file_path).open() as f:
        return yaml.safe_load(f)

def compare_structures(a, b, prefix=""):
    differences = []

    if isinstance(a, Mapping) and isinstance(b, Mapping):
        keys_a = set(a.keys())
        keys_b = set(b.keys())

        for key in keys_a - keys_b:
            full_key = f"{prefix}.{key}" if prefix else key
            differences.append(f"{full_key} only in first file")

        for key in keys_b - keys_a:
            full_key = f"{prefix}.{key}" if prefix else key
            differences.append(f"{full_key} only in second file")

        for key in keys_a & keys_b:
            sub_prefix = f"{prefix}.{key}" if prefix else key
            differences += compare_structures(a[key], b[key], sub_prefix)

    elif isinstance(a, list) and isinstance(b, list):
        set_a = {repr(x) for x in a}
        set_b = {repr(x) for x in b}

        only_in_a = set_a - set_b
        only_in_b = set_b - set_a

        if only_in_a or only_in_b:
            differences.append(f"{prefix} list contents differ:")
            if only_in_a:
                differences.append(f"  items only in first:  {sorted(only_in_a)}")
            if only_in_b:
                differences.append(f"  items only in second: {sorted(only_in_b)}")

    elif a != b:
        differences.append(f"{prefix} value differs:\n    first:  {a}\n    second: {b}")

    return differences

def compare_yaml(file1, file2):
    data1 = load_yaml(file1)
    data2 = load_yaml(file2)

    differences = compare_structures(data1, data2)

    return not differences

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python compare_yaml.py file1.yaml file2.yaml")
    file1, file2 = sys.argv[1], sys.argv[2]
    compare_yaml(file1, file2)
