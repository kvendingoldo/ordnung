#!/usr/bin/env python3
"""
Test cases for file_sorter.py

This module contains comprehensive tests for the file sorting functionality,
including various JSON and YAML structures, edge cases, and batch processing.
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

from ordnung.file_sorter import (
    FileLoadError,
    FileTypeDetectionError,
    detect_file_type,
    find_files,
    load_file,
    save_file,
    sort_dict_recursively,
    sort_file,
)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


data_dir = Path(__file__).parent / "data"


def compare_json_files(f1, f2):
    """Compare two JSON files by content."""
    f1_path = Path(f1)
    f2_path = Path(f2)
    with f1_path.open() as a, f2_path.open() as b:
        return json.load(a) == json.load(b)


def compare_yaml_files(f1, f2):
    """Compare two YAML files by content."""
    f1_path = Path(f1)
    f2_path = Path(f2)
    with f1_path.open() as a, f2_path.open() as b:
        return yaml.safe_load(a) == yaml.safe_load(b)

# File-based tests using input/expected pairs


@pytest.mark.parametrize(("input_file", "expected_file", "compare_fn"), [
    ("json_input1.json", "json_expected1.json", compare_json_files),
    ("json_input2.json", "json_expected2.json", compare_json_files),
    ("json_input3.json", "json_expected3.json", compare_json_files),
    ("json_input4.json", "json_expected4.json", compare_json_files),
    ("json_input5.json", "json_expected5.json", compare_json_files),
    ("yaml_input1.yaml", "yaml_expected1.yaml", compare_yaml_files),
    ("yaml_input2.yaml", "yaml_expected2.yaml", compare_yaml_files),
    ("yaml_input3.yaml", "yaml_expected3.yaml", compare_yaml_files),
    ("yaml_input4.yaml", "yaml_expected4.yaml", compare_yaml_files),
    ("yaml_input5.yaml", "yaml_expected5.yaml", compare_yaml_files),
])
def test_file_sorter_file_based(input_file, expected_file, compare_fn):
    """Test file-based sorting with input/expected file pairs."""
    temp_dir = tempfile.mkdtemp()
    try:
        input_path = data_dir / input_file
        expected_path = data_dir / expected_file
        temp_file = Path(temp_dir) / input_file
        shutil.copy(input_path, temp_file)
        sort_file(str(temp_file))
        assert compare_fn(temp_file, expected_path)
    finally:
        shutil.rmtree(temp_dir)

# Integration tests for batch processing


@pytest.mark.integration
def test_directory_processing():
    """Test processing all files in a directory."""
    temp_dir = tempfile.mkdtemp()
    try:
        # Create test directory structure
        test_dir = Path(temp_dir) / "test_dir"
        test_dir.mkdir()

        # Copy test files
        for i in range(1, 4):
            shutil.copy(
                data_dir / f"json_input{i}.json", test_dir / f"file{i}.json")
            shutil.copy(
                data_dir / f"yaml_input{i}.yaml", test_dir / f"file{i}.yaml")

        # Process directory
        files = find_files([str(test_dir)], recursive=False)
        assert len(files) == 6  # 3 JSON + 3 YAML files

        # Sort each file
        for f in files:
            sort_file(str(f))

        # Verify results
        for i in range(1, 4):
            json_file = test_dir / f"file{i}.json"
            yaml_file = test_dir / f"file{i}.yaml"

            assert compare_json_files(
                json_file, data_dir / f"json_expected{i}.json")
            assert compare_yaml_files(
                yaml_file, data_dir / f"yaml_expected{i}.yaml")
    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.integration
def test_recursive_directory_processing():
    """Test recursive directory processing."""
    temp_dir = tempfile.mkdtemp()
    try:
        # Create nested directory structure
        root_dir = Path(temp_dir) / "root"
        sub_dir = root_dir / "subdir"
        sub_dir.mkdir(parents=True)

        # Add files at different levels
        shutil.copy(data_dir / "json_input1.json", root_dir / "root.json")
        shutil.copy(data_dir / "yaml_input1.yaml", root_dir / "root.yaml")
        shutil.copy(data_dir / "json_input2.json", sub_dir / "sub.json")
        shutil.copy(data_dir / "yaml_input2.yaml", sub_dir / "sub.yaml")

        # Process recursively
        files = find_files([str(root_dir)], recursive=True)
        assert len(files) == 4

        # Sort all files
        for f in files:
            sort_file(str(f))

        # Verify results
        assert compare_json_files(
            root_dir / "root.json", data_dir / "json_expected1.json")
        assert compare_yaml_files(
            root_dir / "root.yaml", data_dir / "yaml_expected1.yaml")
        assert compare_json_files(
            sub_dir / "sub.json", data_dir / "json_expected2.json")
        assert compare_yaml_files(
            sub_dir / "sub.yaml", data_dir / "yaml_expected2.yaml")
    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.integration
def test_glob_pattern_processing():
    """Test glob pattern processing."""
    temp_dir = tempfile.mkdtemp()
    try:
        # Create test files with different extensions
        test_dir = Path(temp_dir) / "test"
        test_dir.mkdir()

        # Add JSON files
        for i in range(1, 4):
            shutil.copy(
                data_dir / f"json_input{i}.json", test_dir / f"data_{i}.json")

        # Add YAML files
        for i in range(1, 3):
            shutil.copy(
                data_dir / f"yaml_input{i}.yaml", test_dir / f"config_{i}.yaml")

        # Add non-matching files
        (test_dir / "readme.txt").write_text("not a json/yaml file")
        (test_dir / "script.py").write_text("# python file")

        # Test JSON-only pattern
        json_files = find_files([str(test_dir / "*.json")], pattern_mode=True)
        assert len(json_files) == 3

        # Test YAML-only pattern
        yaml_files = find_files([str(test_dir / "*.yaml")], pattern_mode=True)
        assert len(yaml_files) == 2

        # Test mixed pattern
        all_files = find_files([str(test_dir / "*.*")], pattern_mode=True)
        assert len(all_files) == 5  # Only JSON/YAML files
    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.integration
def test_regex_filtering():
    """Test regex-based file filtering."""
    temp_dir = tempfile.mkdtemp()
    try:
        test_dir = Path(temp_dir) / "test"
        test_dir.mkdir()

        # Create files with different naming patterns
        shutil.copy(data_dir / "json_input1.json",
                    test_dir / "config_prod.json")
        shutil.copy(data_dir / "json_input2.json",
                    test_dir / "config_dev.json")
        shutil.copy(data_dir / "yaml_input1.yaml",
                    test_dir / "settings_prod.yaml")
        shutil.copy(data_dir / "yaml_input2.yaml",
                    test_dir / "settings_dev.yaml")
        shutil.copy(data_dir / "json_input3.json", test_dir / "data.json")

        # Test regex for production files only
        prod_files = find_files([str(test_dir)], regex=r".*_prod\..*")
        assert len(prod_files) == 2

        # Test regex for JSON files only
        json_files = find_files([str(test_dir)], regex=r".*\.json$")
        assert len(json_files) == 3

        # Test regex for specific pattern
        config_files = find_files([str(test_dir)], regex=r"config_.*")
        assert len(config_files) == 2
    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.integration
def test_multiple_input_sources():
    """Test processing multiple input sources simultaneously."""
    temp_dir = tempfile.mkdtemp()
    try:
        # Create multiple directories
        dir1 = Path(temp_dir) / "dir1"
        dir2 = Path(temp_dir) / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        # Add files to different directories
        shutil.copy(data_dir / "json_input1.json", dir1 / "file1.json")
        shutil.copy(data_dir / "yaml_input1.yaml", dir1 / "file1.yaml")
        shutil.copy(data_dir / "json_input2.json", dir2 / "file2.json")
        shutil.copy(data_dir / "yaml_input2.yaml", dir2 / "file2.yaml")

        # Process both directories
        files = find_files([str(dir1), str(dir2)], recursive=False)
        assert len(files) == 4

        # Sort all files
        for f in files:
            sort_file(str(f))

        # Verify results
        assert compare_json_files(
            dir1 / "file1.json", data_dir / "json_expected1.json")
        assert compare_yaml_files(
            dir1 / "file1.yaml", data_dir / "yaml_expected1.yaml")
        assert compare_json_files(
            dir2 / "file2.json", data_dir / "json_expected2.json")
        assert compare_yaml_files(
            dir2 / "file2.yaml", data_dir / "yaml_expected2.yaml")
    finally:
        shutil.rmtree(temp_dir)

# Unit tests for individual functions


def test_detect_file_type_by_extension():
    """Test file type detection by extension."""
    assert detect_file_type("config.yaml") == "yaml"
    assert detect_file_type("config.yml") == "yaml"
    assert detect_file_type("data.json") == "json"


def test_detect_file_type_by_content_json():
    """Test file type detection by JSON content."""
    with patch("pathlib.Path.open", mock_open(read_data='{"key": "value"}')):
        assert detect_file_type("unknown.txt") == "json"

    with patch("pathlib.Path.open", mock_open(read_data="[1, 2, 3]")):
        assert detect_file_type("unknown.txt") == "json"


def test_detect_file_type_by_content_yaml():
    """Test file type detection by YAML content."""
    with patch("pathlib.Path.open", mock_open(read_data="key: value")):
        assert detect_file_type("unknown.txt") == "yaml"

    with patch("pathlib.Path.open", mock_open(read_data="- item1\n- item2")):
        assert detect_file_type("unknown.txt") == "yaml"


def test_detect_file_type_invalid():
    """Test file type detection with invalid content."""
    with patch("pathlib.Path.open", mock_open(read_data="invalid content")), pytest.raises(FileTypeDetectionError, match="Cannot determine file type"):
        detect_file_type("unknown.txt")


def test_sort_dict_recursively_simple_dict():
    """Test sorting a simple dictionary."""
    input_data = {"c": 3, "a": 1, "b": 2}
    expected = {"a": 1, "b": 2, "c": 3}
    assert sort_dict_recursively(input_data) == expected


def test_sort_dict_recursively_nested_dict():
    """Test sorting a nested dictionary."""
    input_data = {
        "z": {"c": 3, "a": 1, "b": 2},
        "x": {"f": 6, "d": 4, "e": 5},
        "y": 10,
    }
    expected = {
        "x": {"d": 4, "e": 5, "f": 6},
        "y": 10,
        "z": {"a": 1, "b": 2, "c": 3},
    }
    assert sort_dict_recursively(input_data) == expected


def test_sort_dict_recursively_list_of_primitives():
    """Test sorting a list of primitive values."""
    input_data = [3, 1, 2, "b", "a", None]
    expected = [1, 2, 3, "a", "b", None]  # None values at the end
    assert sort_dict_recursively(input_data) == expected


def test_sort_dict_recursively_list_of_objects():
    """Test sorting a list of complex objects (should preserve order)."""
    input_data = [
        {"c": 3, "a": 1},
        {"b": 2, "d": 4},
    ]
    expected = [
        {"a": 1, "c": 3},
        {"b": 2, "d": 4},
    ]
    assert sort_dict_recursively(input_data) == expected


def test_sort_dict_recursively_mixed_types():
    """Test sorting with mixed data types."""
    input_data = {
        "list": [3, 1, 2],
        "dict": {"c": 3, "a": 1, "b": 2},
        "nested": {
            "list": ["z", "x", "y"],
            "dict": {"f": 6, "d": 4, "e": 5},
        },
    }
    expected = {
        "dict": {"a": 1, "b": 2, "c": 3},
        "list": [1, 2, 3],
        "nested": {
            "dict": {"d": 4, "e": 5, "f": 6},
            "list": ["x", "y", "z"],
        },
    }
    assert sort_dict_recursively(input_data) == expected


def test_sort_dict_recursively_array_of_objects():
    """Test sorting arrays of objects by first key value."""
    # Test array of objects with same first key
    data = [
        {"name": "Charlie", "age": 30, "city": "Boston"},
        {"name": "Alice", "age": 25, "city": "New York"},
        {"name": "Bob", "age": 35, "city": "Chicago"},
    ]
    result = sort_dict_recursively(data, sort_arrays_by_first_key=True)

    # Should be sorted by "name" (first key) and each object's keys should be sorted
    expected = [
        {"age": 25, "city": "New York", "name": "Alice"},
        {"age": 35, "city": "Chicago", "name": "Bob"},
        {"age": 30, "city": "Boston", "name": "Charlie"},
    ]
    assert result == expected

    # Test array of objects with different first keys (should not sort by first key)
    data2 = [
        {"name": "Charlie", "age": 30},
        {"age": 25, "name": "Alice"},
        {"name": "Bob", "age": 35},
    ]
    result2 = sort_dict_recursively(data2, sort_arrays_by_first_key=True)

    # Should only sort keys within each object, not sort the array
    expected2 = [
        {"age": 30, "name": "Charlie"},
        {"age": 25, "name": "Alice"},
        {"age": 35, "name": "Bob"},
    ]
    assert result2 == expected2

    # Test array with mixed types (should not sort by first key)
    data3 = [
        {"name": "Charlie", "age": 30},
        "not an object",
        {"name": "Alice", "age": 25},
    ]
    result3 = sort_dict_recursively(data3, sort_arrays_by_first_key=True)

    # Should only sort keys within objects, not sort the array
    expected3 = [
        {"age": 30, "name": "Charlie"},
        "not an object",
        {"age": 25, "name": "Alice"},
    ]
    assert result3 == expected3

    # Test array with empty objects (should not sort by first key)
    data4 = [
        {"name": "Charlie", "age": 30},
        {},
        {"name": "Alice", "age": 25},
    ]
    result4 = sort_dict_recursively(data4, sort_arrays_by_first_key=True)

    # Should only sort keys within objects, not sort the array
    expected4 = [
        {"age": 30, "name": "Charlie"},
        {},
        {"age": 25, "name": "Alice"},
    ]
    assert result4 == expected4

    # Test that default behavior (sort_arrays_by_first_key=False) maintains original order
    data5 = [
        {"name": "Charlie", "age": 30, "city": "Boston"},
        {"name": "Alice", "age": 25, "city": "New York"},
        {"name": "Bob", "age": 35, "city": "Chicago"},
    ]
    result5 = sort_dict_recursively(data5, sort_arrays_by_first_key=False)

    # Should maintain original order but sort keys within each object
    expected5 = [
        {"age": 30, "city": "Boston", "name": "Charlie"},
        {"age": 25, "city": "New York", "name": "Alice"},
        {"age": 35, "city": "Chicago", "name": "Bob"},
    ]
    assert result5 == expected5


def test_load_file_json():
    """Test loading JSON file."""
    json_content = '{"c": 3, "a": 1, "b": 2}'
    with patch("pathlib.Path.open", mock_open(read_data=json_content)):
        result = load_file("test.json", "json")
        assert result == {"c": 3, "a": 1, "b": 2}


def test_load_file_yaml():
    """Test loading YAML file."""
    yaml_content = "c: 3\na: 1\nb: 2"
    with patch("pathlib.Path.open", mock_open(read_data=yaml_content)):
        result = load_file("test.yaml", "yaml")
        assert result == {"c": 3, "a": 1, "b": 2}


def test_save_file_json():
    """Test saving JSON file."""
    data = {"a": 1, "b": 2, "c": 3}
    mock_file = mock_open()
    with patch("pathlib.Path.open", mock_file):
        save_file(data, "test.json", "json", json_indent=2)
        mock_file.assert_called_once_with("w", encoding="utf-8")


def test_save_file_yaml():
    """Test saving YAML file."""
    data = {"a": 1, "b": 2, "c": 3}
    mock_file = mock_open()
    with patch("pathlib.Path.open", mock_file):
        save_file(data, "test.yaml", "yaml", yaml_indent=2)
        mock_file.assert_called_once_with("w", encoding="utf-8")

# Error handling tests


def test_invalid_json(tmp_path):
    """Test handling of invalid JSON files."""
    file = tmp_path / "bad.json"
    file.write_text("{invalid json}")
    with pytest.raises(FileLoadError):
        sort_file(str(file))


def test_invalid_yaml(tmp_path):
    """Test handling of invalid YAML files."""
    file = tmp_path / "bad.yaml"
    file.write_text("invalid: yaml: content:")
    with pytest.raises(FileLoadError):
        sort_file(str(file))


def test_empty_file(tmp_path):
    """Test handling of empty files."""
    file = tmp_path / "empty.json"
    file.write_text("")
    with pytest.raises(FileLoadError):
        sort_file(str(file))


def test_file_not_found():
    """Test handling of non-existent files."""
    with pytest.raises(FileNotFoundError):
        sort_file("/no/such/file.json")


def test_no_matching_files():
    """Test handling when no matching files are found."""
    temp_dir = tempfile.mkdtemp()
    try:
        # Create directory with no JSON/YAML files
        test_dir = Path(temp_dir) / "empty"
        test_dir.mkdir()
        (test_dir / "readme.txt").write_text("no json/yaml here")

        files = find_files([str(test_dir)], recursive=False)
        assert len(files) == 0
    finally:
        shutil.rmtree(temp_dir)

# Edge case tests


def test_unicode_content():
    """Test sorting with Unicode content."""
    temp_dir = tempfile.mkdtemp()
    try:
        file = Path(temp_dir) / "unicode.json"
        input_data = {
            "café": "coffee",
            "naïve": "innocent",
            "résumé": "summary",
            "a": "first",
        }

        with file.open("w", encoding="utf-8") as f:
            json.dump(input_data, f, ensure_ascii=False)

        sort_file(str(file))

        with file.open(encoding="utf-8") as f:
            result = json.load(f)

        expected_keys = ["a", "café", "naïve", "résumé"]
        assert list(result.keys()) == expected_keys
    finally:
        shutil.rmtree(temp_dir)


def test_none_values():
    """Test sorting with None values."""
    temp_dir = tempfile.mkdtemp()
    try:
        file = Path(temp_dir) / "nulls.json"
        input_data = {
            "c": None,
            "a": 1,
            "b": None,
            "d": 2,
        }

        with file.open("w") as f:
            json.dump(input_data, f)

        sort_file(str(file))

        with file.open() as f:
            result = json.load(f)

        expected = {
            "a": 1,
            "b": None,
            "c": None,
            "d": 2,
        }
        assert result == expected
    finally:
        shutil.rmtree(temp_dir)


def test_numbers_as_strings():
    """Test sorting with numbers as strings."""
    temp_dir = tempfile.mkdtemp()
    try:
        file = Path(temp_dir) / "numbers.json"
        input_data = {
            "10": "ten",
            "2": "two",
            "1": "one",
            "20": "twenty",
        }

        with file.open("w") as f:
            json.dump(input_data, f)

        sort_file(str(file))

        with file.open() as f:
            result = json.load(f)

        expected_keys = ["1", "10", "2", "20"]  # String sorting
        assert list(result.keys()) == expected_keys
    finally:
        shutil.rmtree(temp_dir)


def test_empty_structures():
    """Test sorting empty structures."""
    temp_dir = tempfile.mkdtemp()
    try:
        file = Path(temp_dir) / "empty.json"
        input_data = {
            "empty_dict": {},
            "empty_list": [],
            "nested_empty": {
                "empty_dict": {},
                "empty_list": [],
            },
        }

        with file.open("w") as f:
            json.dump(input_data, f)

        sort_file(str(file))

        with file.open() as f:
            result = json.load(f)

        assert result == input_data  # Should be unchanged
    finally:
        shutil.rmtree(temp_dir)


def test_invalid_json_file(tmp_path):
    """Test that an invalid JSON file raises an error."""
    file = tmp_path / "bad.json"
    file.write_text("{invalid json}")
    with pytest.raises(FileLoadError):
        sort_file(str(file))


def test_invalid_yaml_file(tmp_path):
    """Test that an invalid YAML file raises an error."""
    file = tmp_path / "bad.yaml"
    file.write_text("a: 1\nb: [2, 3\nc: 4")  # Missing closing bracket
    with pytest.raises(FileLoadError):
        sort_file(str(file))

# Check mode tests


def test_check_mode_formatted_file(tmp_path):
    """Test check mode with an already formatted file."""
    file = tmp_path / "formatted.json"
    # Use the actual formatted output that the sorter produces
    formatted_content = '{\n  "a": 1,\n  "b": 2,\n  "c": 3\n}'
    file.write_text(formatted_content)

    # Should return True (file is formatted)
    result = sort_file(str(file), check=True)
    assert result is True


def test_check_mode_unformatted_file(tmp_path):
    """Test check mode with an unformatted file."""
    file = tmp_path / "unformatted.json"
    unformatted_content = '{"c": 3, "a": 1, "b": 2}'
    file.write_text(unformatted_content)

    # Should return False (file is not formatted)
    result = sort_file(str(file), check=True)
    assert result is False

    # File should not be changed
    with file.open() as f:
        content = f.read()
    assert content == unformatted_content


def test_check_mode_yaml_formatted(tmp_path):
    """Test check mode with formatted YAML file."""
    file = tmp_path / "formatted.yaml"
    # Use the actual formatted output that the sorter produces
    formatted_content = "a: 1\nb: 2\nc: 3\n"
    file.write_text(formatted_content)

    result = sort_file(str(file), check=True)
    assert result is True


def test_check_mode_yaml_unformatted(tmp_path):
    """Test check mode with unformatted YAML file."""
    file = tmp_path / "unformatted.yaml"
    unformatted_content = "c: 3\na: 1\nb: 2\n"
    file.write_text(unformatted_content)

    result = sort_file(str(file), check=True)
    assert result is False

    # File should not be changed
    with file.open() as f:
        content = f.read()
    assert content == unformatted_content


def test_check_mode_with_different_indentation(tmp_path):
    """Test check mode with files that have different indentation."""
    file = tmp_path / "different_indent.json"
    # File with 4-space indentation
    content_4spaces = '{\n    "a": 1,\n    "b": 2,\n    "c": 3\n}'
    file.write_text(content_4spaces)

    # Check with default 2-space indentation (should fail)
    result = sort_file(str(file), check=True, json_indent=2)
    assert result is False

    # Check with 4-space indentation (should pass)
    result = sort_file(str(file), check=True, json_indent=4)
    assert result is True


def test_check_mode_complex_structure(tmp_path):
    """Test check mode with complex nested structures."""
    file = tmp_path / "complex.json"
    unformatted_content = """{
  "z": {"c": 3, "a": 1, "b": 2},
  "x": {"f": 6, "d": 4, "e": 5},
  "y": 10
}"""
    file.write_text(unformatted_content)

    # Should detect as unformatted
    result = sort_file(str(file), check=True)
    assert result is False


def test_check_mode_empty_file(tmp_path):
    """Test check mode with empty file."""
    file = tmp_path / "empty.json"
    file.write_text("")

    # Should raise exception
    with pytest.raises(FileLoadError):
        sort_file(str(file), check=True)


def test_check_mode_with_lists(tmp_path):
    """Test check mode with files containing unsorted lists."""
    file = tmp_path / "lists.json"
    unformatted_content = '{"numbers": [3, 1, 2], "letters": ["c", "a", "b"]}'
    file.write_text(unformatted_content)

    result = sort_file(str(file), check=True)
    assert result is False


def test_check_mode_mixed_content(tmp_path):
    """Test check mode with mixed content (some formatted, some not)."""
    # Create a directory with mixed files
    test_dir = tmp_path / "mixed"
    test_dir.mkdir()

    # Formatted file - use actual sorter output
    formatted_file = test_dir / "formatted.json"
    formatted_file.write_text('{\n  "a": 1,\n  "b": 2,\n  "c": 3\n}')

    # Unformatted file
    unformatted_file = test_dir / "unformatted.json"
    unformatted_file.write_text('{"c": 3, "a": 1, "b": 2}')

    # Check formatted file
    result1 = sort_file(str(formatted_file), check=True)
    assert result1 is True

    # Check unformatted file
    result2 = sort_file(str(unformatted_file), check=True)
    assert result2 is False


def test_check_mode_preserves_file_content(tmp_path):
    """Test that check mode doesn't modify file content."""
    file = tmp_path / "preserve.json"
    original_content = '{"c": 3, "a": 1, "b": 2, "d": 4}'
    file.write_text(original_content)

    # Run check mode
    sort_file(str(file), check=True)

    # Verify content is unchanged
    with file.open() as f:
        content = f.read()
    assert content == original_content


def test_check_mode_with_none_values(tmp_path):
    """Test check mode with files containing None values."""
    file = tmp_path / "nulls.json"
    unformatted_content = '{"c": null, "a": 1, "b": null, "d": 2}'
    file.write_text(unformatted_content)

    result = sort_file(str(file), check=True)
    assert result is False


def test_check_mode_with_unicode(tmp_path):
    """Test check mode with Unicode content."""
    file = tmp_path / "unicode.json"
    unformatted_content = '{"café": "coffee", "a": "first", "naïve": "innocent"}'
    file.write_text(unformatted_content)

    result = sort_file(str(file), check=True)
    assert result is False


def test_empty_json_file(tmp_path):
    file = tmp_path / "empty.json"
    file.write_text("")
    with pytest.raises(FileLoadError):
        sort_file(str(file))


def test_check_mode_invalid_yaml(tmp_path):
    file = tmp_path / "bad.yaml"
    file.write_text("a: 1\nb: [2, 3\nc: 4")
    with pytest.raises(FileLoadError):
        sort_file(str(file), check=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
