#!/usr/bin/env python3
"""
Test cases for file_sorter.py

This module contains comprehensive tests for the file sorting functionality,
including various JSON and YAML structures, edge cases, and batch processing.
"""

import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

from ordnung.file_sorter import (
    FileLoadError,
    sort_file,
)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

data_dir = Path(__file__).parent / "data" / "pass"
fail_dir = Path(__file__).parent / "data" / "fail"


def compare_json_files(f1, f2):
    """Compare two JSON files by content."""
    with Path(f1).open() as a, Path(f2).open() as b:
        return json.load(a) == json.load(b)


def compare_yaml_files(f1, f2):
    """Compare two YAML files by loading them as objects."""
    with Path(f1).open() as a, Path(f2).open() as b:
        return yaml.safe_load(a) == yaml.safe_load(b)


def create_pass_test(input_file, expected_file, ext):
    """Create a test function for files that should pass sorting."""
    def test_func(tmp_path, input_file=input_file, expected_file=expected_file, ext=ext):
        input_path = data_dir / input_file
        temp_file = tmp_path / input_file
        shutil.copy(input_path, temp_file)
        sort_file(str(temp_file))
        expected_path = data_dir / expected_file
        assert expected_path.exists(
        ), f"Expected file {expected_file} does not exist!"
        if ext == ".json":
            assert compare_json_files(temp_file, expected_path)
        else:
            assert compare_yaml_files(temp_file, expected_path)
    return test_func


def create_fail_test(input_file):
    """Create a test function for files that should fail sorting."""
    def test_func(tmp_path, input_file=input_file):
        input_path = fail_dir / input_file
        temp_file = tmp_path / input_file
        shutil.copy(input_path, temp_file)
        # This file should have invalid syntax and fail
        with pytest.raises(FileLoadError):
            sort_file(str(temp_file))
    return test_func


# Auto-generate tests for each input file in pass/
pass_input_files = [f for f in data_dir.iterdir() if f.name.endswith(
    ("_input.json", "_input.yaml"))]

for input_file in pass_input_files:
    if input_file.name.endswith("_input.json"):
        base = input_file.name[:-11]  # Remove '_input.json'
        ext = ".json"
    elif input_file.name.endswith("_input.yaml"):
        base = input_file.name[:-11]  # Remove '_input.yaml'
        ext = ".yaml"
    else:
        continue
    expected_file = f"{base}_expected{ext}"

    test_func = create_pass_test(input_file.name, expected_file, ext)
    test_func.__name__ = f"test_{base}"
    test_func.__doc__ = f"Test sorting for {input_file.name}."
    globals()[f"test_{base}"] = test_func


# Auto-generate tests for each input file in fail/
fail_input_files = [f for f in fail_dir.iterdir() if f.name.endswith(
    ("_input.json", "_input.yaml"))]

for input_file in fail_input_files:
    if input_file.name.endswith("_input.json"):
        base = input_file.name[:-11]  # Remove '_input.json'
    elif input_file.name.endswith("_input.yaml"):
        base = input_file.name[:-11]  # Remove '_input.yaml'
    else:
        continue

    test_func = create_fail_test(input_file.name)
    test_func.__name__ = f"test_{base}"
    test_func.__doc__ = f"Test that {input_file.name} fails as expected."
    globals()[f"test_{base}"] = test_func
