#!/usr/bin/env python3
"""
File Sorter - A utility to sort YAML and JSON files.

This script takes a YAML or JSON file as input, sorts its contents,
and writes the sorted result back to the original file or a specified output file.
"""

import argparse
import difflib
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, List, Optional

import yaml

# Configure YAML to handle Norway problem correctly


class NorwaySafeLoader(yaml.SafeLoader):
    """Custom SafeLoader that treats off/no/n/on/yes/y as strings to avoid Norway problem."""

    def construct_yaml_bool(self, node):
        """Override boolean construction to handle Norway problem."""
        value = self.construct_scalar(node)
        if value in ["off", "no", "n", "on", "yes", "y"]:
            # These should be treated as strings, not booleans
            return value
        # For actual boolean values, use the standard behavior
        if value in ["true", "false"]:
            return value == "true"
        return value

    def construct_undefined(self, node):
        """Handle undefined tags by treating them as strings."""
        return self.construct_scalar(node)

    def fetch_alias(self):
        """Override to handle glob patterns that start with *."""
        # Check if the next token looks like a glob pattern
        if self.peek() == "*" and self.peek(1) == ".":
            # This is likely a glob pattern, not an alias
            # Skip the alias parsing and treat as a regular scalar
            return self.fetch_plain()
        return super().fetch_alias()

    def construct_yaml_timestamp(self, node):
        """Override timestamp construction to handle port mappings like 22:22 as strings."""
        value = self.construct_scalar(node)
        # If it looks like a port mapping (number:number), treat as string
        if ":" in value and len(value.split(":")) == 2:
            parts = value.split(":")
            if parts[0].isdigit() and parts[1].isdigit():
                # This looks like a port mapping, keep as string
                return value
        # For actual timestamps, use standard behavior
        return super().construct_yaml_timestamp(node)


# Add multi-constructor for unknown tags
def unknown_tag_constructor(loader, _tag_suffix, node):
    """Handle unknown tags by treating them as strings."""
    return loader.construct_scalar(node)


NorwaySafeLoader.add_multi_constructor("!", unknown_tag_constructor)


# Remove the implicit resolver for timestamps from NorwaySafeLoader for all keys, including None
for ch in list(NorwaySafeLoader.yaml_implicit_resolvers):
    resolvers = NorwaySafeLoader.yaml_implicit_resolvers[ch]
    NorwaySafeLoader.yaml_implicit_resolvers[ch] = [
        (tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"
    ]
# Also remove for None key
if None in NorwaySafeLoader.yaml_implicit_resolvers:
    resolvers = NorwaySafeLoader.yaml_implicit_resolvers[None]
    NorwaySafeLoader.yaml_implicit_resolvers[None] = [
        (tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"
    ]


class NorwaySafeDumper(yaml.SafeDumper):
    def represent_str(self, data):
        if data in {"off", "no", "n", "on", "yes", "y"}:
            return self.represent_scalar("tag:yaml.org,2002:str", data, style="'")
        # Check if the string contains newlines and should be a block scalar
        if "\n" in data:
            return self.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return super().represent_str(data)

    def represent_none(self, _):
        """Represent None as empty value instead of explicit null."""
        return self.represent_scalar("tag:yaml.org,2002:null", "")


# Register the custom string representer
NorwaySafeDumper.add_representer(str, NorwaySafeDumper.represent_str)
# Register the custom None representer
NorwaySafeDumper.add_representer(type(None), NorwaySafeDumper.represent_none)

# Set up logger
logger = logging.getLogger("ordnung")


class FileSorterError(Exception):
    """Base exception for file sorter errors."""


class FileTypeDetectionError(FileSorterError):
    """Raised when file type cannot be determined."""


class FileLoadError(FileSorterError):
    """Raised when file cannot be loaded."""


class FileSaveError(FileSorterError):
    """Raised when file cannot be saved."""


def detect_file_type(file_path: str) -> str:
    path = Path(file_path)
    extension = path.suffix.lower()
    if extension in [".yaml", ".yml"]:
        return "yaml"
    if extension == ".json":
        return "json"
    try:
        with path.open(encoding="utf-8") as f:
            content = f.read().strip()
        if content.startswith(("{", "[")):
            return "json"
        if content.startswith("-") or ":" in content:
            return "yaml"
        raise FileTypeDetectionError(
            f"Cannot determine file type for {file_path}")
    except Exception as err:
        raise FileTypeDetectionError(
            f"Cannot determine file type for {file_path}") from err


def validate_data_preservation(original: Any, sorted_data: Any, path: str = "root") -> List[str]:
    """
    Validate that all data structures, keys, and values are preserved after sorting.

    Args:
        original: The original data structure
        sorted_data: The sorted data structure
        path: Current path in the data structure (for error reporting)

    Returns:
        List of validation errors (empty if validation passes)
    """
    errors = []

    # Check if types match
    if type(original) is not type(sorted_data):
        errors.append(
            f"Type mismatch at {path}: {type(original).__name__} vs {type(sorted_data).__name__}")
        return errors

    if isinstance(original, dict):
        # Check that all keys are preserved
        original_keys = set(original.keys())
        sorted_keys = set(sorted_data.keys())

        missing_keys = original_keys - sorted_keys
        extra_keys = sorted_keys - original_keys

        if missing_keys:
            errors.append(f"Missing keys at {path}: {sorted(missing_keys)}")
        if extra_keys:
            errors.append(f"Extra keys at {path}: {sorted(extra_keys)}")

        # Recursively validate values for common keys
        common_keys = original_keys & sorted_keys
        for key in common_keys:
            key_path = f"{path}.{key}" if path != "root" else key
            errors.extend(validate_data_preservation(
                original[key], sorted_data[key], key_path))

    elif isinstance(original, list):
        # Check that all elements are preserved (order may differ)
        if len(original) != len(sorted_data):
            errors.append(
                f"Length mismatch at {path}: {len(original)} vs {len(sorted_data)}")
            return errors

        # For lists, we need to check that all elements exist (order may be different)
        # Convert to sets for comparison, but handle unhashable types
        try:
            original_set = set(original)
            sorted_set = set(sorted_data)

            missing_elements = original_set - sorted_set
            extra_elements = sorted_set - original_set

            if missing_elements:
                errors.append(
                    f"Missing elements at {path}: {sorted(missing_elements)}")
            if extra_elements:
                errors.append(
                    f"Extra elements at {path}: {sorted(extra_elements)}")
        except TypeError:
            # Handle unhashable types by comparing element by element
            # This is less efficient but handles complex nested structures
            original_copy = original.copy()
            sorted_copy = sorted_data.copy()

            for i, orig_elem in enumerate(original_copy):
                found_match = False
                for j, sorted_elem in enumerate(sorted_copy):
                    elem_errors = validate_data_preservation(
                        orig_elem, sorted_elem, f"{path}[{i}]")
                    if not elem_errors:
                        sorted_copy.pop(j)
                        found_match = True
                        break

                if not found_match:
                    errors.append(
                        f"Element at {path}[{i}] not found in sorted data: {orig_elem}")

    # For primitive types, check exact equality
    elif original != sorted_data:
        errors.append(
            f"Value mismatch at {path}: {original} vs {sorted_data}")

    return errors


def sort_dict_recursively(data: Any, *, sort_arrays_by_first_key: bool = False) -> Any:
    if isinstance(data, dict):
        return {k: sort_dict_recursively(v, sort_arrays_by_first_key=sort_arrays_by_first_key) for k, v in sorted(data.items(), key=lambda x: str(x[0]))}
    if isinstance(data, list):
        if all(isinstance(item, (str, int, float, bool)) or item is None for item in data):
            # Sort arrays of primitives
            return sorted(data, key=lambda x: (x is None, str(x) if x is not None else ""))
        # For arrays of objects, optionally sort by the first key's value, then recursively sort each object
        if sort_arrays_by_first_key and all(isinstance(item, dict) and item for item in data):
            # Get the first key from each dict and sort by its value BEFORE sorting keys within objects
            first_keys = [next(iter(item.keys())) for item in data]
            # Use the first key that appears in all items, or the first key of the first item
            if first_keys and all(k == first_keys[0] for k in first_keys):
                sort_key = first_keys[0]
                # Sort the array by the first key's value
                sorted_array = sorted(data, key=lambda x: (
                    x[sort_key] is None, str(x[sort_key]) if x[sort_key] is not None else ""))
                # Then recursively sort each object's keys
                return [sort_dict_recursively(item, sort_arrays_by_first_key=sort_arrays_by_first_key) for item in sorted_array]
        # If not sorting by first key or not all items are dicts with the same first key, just recursively sort each item
        return [sort_dict_recursively(item, sort_arrays_by_first_key=sort_arrays_by_first_key) for item in data]
    return data


def load_file(file_path: str, file_type: str) -> Any:
    def quote_port_and_specials(yaml_text: str) -> str:
        # Only quote if not already quoted (not surrounded by single or double quotes)
        # 1. Port mappings in sequences: - 22:22
        yaml_text = re.sub(r"^([ \t]*-[ \t]*)(?!['\"])(\d{1,5}:\d{1,5})(?!['\"])([ \t]*)(#.*)?$",
                           lambda m: f"{m.group(1)}'{m.group(2)}'{m.group(3) or ''}{m.group(4) or ''}",
                           yaml_text, flags=re.MULTILINE)
        # 2. !something in sequences: - !.git
        yaml_text = re.sub(r"^([ \t]*-[ \t]*)(?!['\"])(!\S+)(?!['\"])([ \t]*)(#.*)?$",
                           lambda m: f"{m.group(1)}'{m.group(2)}'{m.group(3) or ''}{m.group(4) or ''}",
                           yaml_text, flags=re.MULTILINE)
        # 3. Norway-problem values in sequences: - off, - no, - n, - on, - yes, - y
        np_words = r"(off|no|n|on|yes|y)"
        yaml_text = re.sub(rf"^([ \t]*-[ \t]*)(?<!['\"])(?P<val>{np_words})(?!['\"])([ \t]*)(#.*)?$",
                           lambda m: f"{m.group(1)}'{m.group('val')}'{m.group(4) or ''}{m.group(5) or ''}",
                           yaml_text, flags=re.MULTILINE)
        # 4. Norway-problem values in mappings: key: off
        return re.sub(rf"^([ \t]*[\w\-]+:[ \t]*)(?<!['\"])(?P<val>{np_words})(?!['\"])([ \t]*)(#.*)?$",
                      lambda m: f"{m.group(1)}'{m.group('val')}'{m.group(4) or ''}{m.group(5) or ''}",
                      yaml_text, flags=re.MULTILINE)
    try:
        with Path(file_path).open(encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                raise FileLoadError(f"File is empty: {file_path}")
            f.seek(0)
            if file_type == "json":
                return json.load(f)
            if file_type == "yaml":
                # Preprocess to quote unquoted port mappings, !something, and Norway-problem values
                content = quote_port_and_specials(content)
                # nosec
                docs = list(yaml.load_all(content, Loader=NorwaySafeLoader))
                if len(docs) == 1:
                    return docs[0]
                return docs
    except Exception as err:
        raise FileLoadError(
            f"Error loading {file_type.upper()} file: {err}") from err


def save_file(data: Any, file_path: str, file_type: str, json_indent: int = 2, yaml_indent: int = 2) -> None:
    try:
        with Path(file_path).open("w", encoding="utf-8") as f:
            if file_type == "json":
                json.dump(data, f, indent=json_indent,
                          ensure_ascii=False, sort_keys=True)
            elif file_type == "yaml":
                # Support multiple YAML documents
                # Avoid writing a single YAML doc containing a list of docs
                if isinstance(data, list) and (len(data) > 1 or (len(data) == 1 and not isinstance(data[0], list))):
                    yaml.dump_all(data, f, default_flow_style=False,
                                  allow_unicode=True, sort_keys=True, indent=yaml_indent, Dumper=NorwaySafeDumper, explicit_start=True)
                else:
                    yaml.dump(data, f, default_flow_style=False,
                              allow_unicode=True, sort_keys=True, indent=yaml_indent, Dumper=NorwaySafeDumper)
    except Exception as err:
        raise FileSaveError(
            f"Error saving {file_type.upper()} file: {err}") from err


def sort_file(input_file: str, output_file: Optional[str] = None, *, json_indent: int = 2, yaml_indent: int = 2, check: bool = False, sort_arrays_by_first_key: bool = False, sort_docs_by_first_key: bool = False, validate: bool = False) -> bool:
    """
    Sort a JSON or YAML file. For YAML, can sort arrays by first key and (if multi-doc) sort docs by first key value.
    Args:
        input_file: Path to input file.
        output_file: Path to output file (or None to overwrite input).
        json_indent: Indentation for JSON output.
        yaml_indent: Indentation for YAML output.
        check: If True, only check formatting, don't write.
        sort_arrays_by_first_key: If True, sort arrays of objects by their first key value.
        sort_docs_by_first_key: If True and YAML multi-doc, sort docs by the value of their first key.
        validate: If True, validate that all data structures are preserved after sorting.
    Returns:
        True if file is already formatted (in check mode), else True if write succeeds.
    """
    if not Path(input_file).exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    file_type = detect_file_type(input_file)
    logger.info("Detected file type: %s", file_type.upper())
    data = load_file(input_file, file_type)
    logger.info("Loaded data from: %s", input_file)
    # If YAML multi-doc: sort each doc separately
    if file_type == "yaml" and isinstance(data, list) and any(isinstance(doc, (dict, list, type(None))) for doc in data):
        sorted_docs = [sort_dict_recursively(
            doc, sort_arrays_by_first_key=sort_arrays_by_first_key) for doc in data]
        if sort_docs_by_first_key:
            # Only sort docs that are dicts and have at least one key

            def doc_sort_key(doc):
                if isinstance(doc, dict) and doc:
                    first_key = next(iter(doc.keys()))
                    value = doc[first_key]
                    # Sort by (type_name, string_value) for robust, user-explained order
                    return (str(type(value)), str(value))
                # None or non-dict docs sort last
                return chr(0x10FFFF)
            sorted_data = sorted(sorted_docs, key=doc_sort_key)
        else:
            sorted_data = sorted_docs
    else:
        sorted_data = sort_dict_recursively(
            data, sort_arrays_by_first_key=sort_arrays_by_first_key)
    logger.info("Data sorted successfully")

    # Validate data preservation if requested
    if validate:
        logger.info("Validating data preservation...")
        validation_errors = validate_data_preservation(data, sorted_data)
        if validation_errors:
            logger.error(
                "Data validation failed! The following issues were found:")
            for error in validation_errors:
                logger.error("  %s", error)
            raise FileSorterError(
                "Data validation failed - data structures were not preserved during sorting")
        logger.info("Data validation passed - all structures preserved")

    if check:
        # Check mode: compare sorted output to file content
        with Path(input_file).open(encoding="utf-8") as f:
            original_content = f.read().strip()
        if file_type == "json":
            formatted = json.dumps(
                sorted_data, indent=json_indent, ensure_ascii=False, sort_keys=True)
        # For multi-doc YAML, use dump_all
        elif isinstance(sorted_data, list) and any(isinstance(doc, (dict, list, type(None))) for doc in sorted_data):
            formatted = yaml.dump_all(sorted_data, default_flow_style=False,
                                      allow_unicode=True, sort_keys=True, indent=yaml_indent).strip()
        else:
            formatted = yaml.dump(sorted_data, default_flow_style=False,
                                  allow_unicode=True, sort_keys=True, indent=yaml_indent).strip()
        if original_content != formatted:
            logger.warning("File is not formatted: %s", input_file)
            diff = difflib.unified_diff(
                original_content.splitlines(),
                formatted.splitlines(),
                fromfile="original",
                tofile="sorted",
                lineterm="",
            )
            logger.info("\n".join(diff))
            return False
        logger.info("File is already formatted: %s", input_file)
        return True
    # Normal mode: write output
    if output_file is None:
        output_file = input_file
        logger.info("Writing sorted data back to: %s", output_file)
    else:
        logger.info("Writing sorted data to: %s", output_file)
    save_file(sorted_data, output_file, file_type, json_indent, yaml_indent)
    logger.info("File saved successfully!")
    return True


def _should_exclude_file(file_path: Path, exclude_patterns: Optional[List[str]]) -> bool:
    """
    Check if a file should be excluded based on the exclude patterns.
    Supports both glob patterns and regex patterns.
    """
    if not exclude_patterns:
        return False

    file_str = str(file_path)
    file_name = file_path.name

    for pattern in exclude_patterns:
        # Try glob pattern matching first
        try:
            if file_path.match(pattern):
                return True
        except (ValueError, TypeError):
            # If glob matching fails, try regex
            pass

        # Try regex pattern matching
        try:
            if re.search(pattern, file_str) or re.search(pattern, file_name):
                return True
        except re.error:
            # If regex is invalid, treat as literal string match
            if pattern in file_str or pattern in file_name:
                return True

    return False


def find_files(
    paths: List[str],
    *, recursive: bool = False,
    regex: Optional[str] = None,
    pattern_mode: bool = False,
    exclude_patterns: Optional[List[str]] = None,
) -> List[Path]:
    """
    Given a list of files, directories, or patterns, return all matching YAML/JSON files.
    """
    found = set()
    regex_compiled = re.compile(regex) if regex else None
    for p in paths:
        path = Path(p)
        if pattern_mode:
            parent = path.parent if path.parent != Path() else Path()
            pattern = path.name
            matches = parent.rglob(
                pattern) if recursive else parent.glob(pattern)
            for match_path in matches:
                if (
                    match_path.is_file()
                    and match_path.suffix.lower() in {".json", ".yaml", ".yml"}
                    and (not regex_compiled or regex_compiled.search(str(match_path)))
                    and not _should_exclude_file(match_path, exclude_patterns)
                ):
                    found.add(match_path.resolve())
        elif path.is_file():
            if (
                path.suffix.lower() in {".json", ".yaml", ".yml"}
                and (not regex_compiled or regex_compiled.search(str(path)))
                and not _should_exclude_file(path, exclude_patterns)
            ):
                found.add(path.resolve())
        elif path.is_dir():
            for ext in ("*.json", "*.yaml", "*.yml"):
                files = path.rglob(ext) if recursive else path.glob(ext)
                for f in files:
                    if f.is_file() and (not regex_compiled or regex_compiled.search(str(f))) and not _should_exclude_file(f, exclude_patterns):
                        found.add(f.resolve())
        else:
            parent = path.parent if path.parent != Path() else Path()
            pattern = path.name
            matches = parent.rglob(
                pattern) if recursive else parent.glob(pattern)
            for match_path in matches:
                if (
                    match_path.is_file()
                    and match_path.suffix.lower() in {".json", ".yaml", ".yml"}
                    and (not regex_compiled or regex_compiled.search(str(match_path)))
                    and not _should_exclude_file(match_path, exclude_patterns)
                ):
                    found.add(match_path.resolve())
    return sorted(found)


def main():
    parser = argparse.ArgumentParser(
        description="Sort YAML and JSON files alphabetically by keys. Supports single files, multiple files, directories, and glob patterns.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sort single files
  ordnung config.json
  ordnung settings.yaml

  # Sort multiple files
  ordnung file1.json file2.yaml file3.yml

  # Sort all JSON/YAML files in a directory
  ordnung ./configs --recursive

  # Use glob patterns to find files
  ordnung './data/**/*.json' --pattern
  ordnung './configs/*.yaml' --pattern

  # Filter files with regex
  ordnung ./mydir --regex '.*\\.ya?ml$'
  ordnung ./data --regex '.*_prod\\.json$'

  # Exclude files matching patterns
  ordnung ./data --exclude '*.tmp' --exclude 'backup_*'
  ordnung ./configs --exclude '.*\\.bak$' --recursive

  # Validate data preservation
  ordnung config.json --validate
  ordnung ./data --validate --recursive

  # Check mode (CI): verify formatting without rewriting
  ordnung ./data --check

  # Sort arrays of objects by first key value
  ordnung data.json --sort-arrays-by-first-key

  # Custom indentation
  ordnung config.json --json-indent 4
  ordnung settings.yaml --yaml-indent 4

  # Save to new file
  ordnung input.json -o sorted.json
        """,
    )
    parser.add_argument(
        "inputs", nargs="+",
        help="Input file(s), directory(ies), or glob pattern(s) to process",
    )
    parser.add_argument(
        "-o", "--output", dest="output_file",
        help="Output file path (only for single file input, otherwise files are overwritten)",
    )
    parser.add_argument(
        "--json-indent", type=int, default=2, metavar="SPACES",
        help="Number of spaces for JSON indentation (default: 2)",
    )
    parser.add_argument(
        "--yaml-indent", type=int, default=2, metavar="SPACES",
        help="Number of spaces for YAML indentation (default: 2)",
    )
    parser.add_argument(
        "--recursive", action="store_true",
        help="Recursively search directories for JSON/YAML files",
    )
    parser.add_argument(
        "--pattern", action="store_true",
        help="Treat input arguments as glob patterns (e.g., './**/*.json')",
    )
    parser.add_argument(
        "--regex", type=str, metavar="PATTERN",
        help="Regular expression to filter file paths (e.g., '.*_config\\.ya?ml$')",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Check if files are properly formatted without modifying them (useful for CI)",
    )
    parser.add_argument(
        "--sort-arrays-by-first-key", action="store_true",
        help="Sort arrays of objects by the value of the first key in each object",
    )
    parser.add_argument(
        "--sort-docs-by-first-key", action="store_true",
        help="Sort YAML documents (--- separated) by the value of their first key (default: preserve order)",
    )
    parser.add_argument(
        "--exclude", action="append", metavar="PATTERN",
        help="Exclude files matching pattern (can be used multiple times). Supports glob patterns and regex.",
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Validate that all data structures, keys, and values are preserved after sorting (useful for ensuring no data loss)",
    )
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level (default: INFO)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s: %(message)s",
    )

    files = find_files(
        args.inputs,
        recursive=args.recursive,
        regex=args.regex,
        pattern_mode=args.pattern,
        exclude_patterns=args.exclude,
    )

    if not files:
        logger.error("No matching YAML/JSON files found.")
        sys.exit(1)

    failed = []
    if len(files) == 1 and args.output_file and not args.check:
        # Single file, output specified
        try:
            sort_file(
                str(files[0]),
                args.output_file,
                json_indent=args.json_indent,
                yaml_indent=args.yaml_indent,
                check=False,
                sort_arrays_by_first_key=args.sort_arrays_by_first_key,
                sort_docs_by_first_key=args.sort_docs_by_first_key,
                validate=args.validate,
            )
        except Exception:
            logger.exception("Error processing file")
            sys.exit(1)
    else:
        # Multiple files or check mode
        for f in files:
            try:
                logger.info("\nProcessing: %s", f)
                ok = sort_file(
                    str(f),
                    None,
                    json_indent=args.json_indent,
                    yaml_indent=args.yaml_indent,
                    check=args.check,
                    sort_arrays_by_first_key=args.sort_arrays_by_first_key,
                    sort_docs_by_first_key=args.sort_docs_by_first_key,
                    validate=args.validate,
                )
                if args.check and not ok:
                    failed.append(str(f))
            except Exception:
                logger.exception("Error processing %s", f)
                if args.check:
                    failed.append(str(f))

        if args.check:
            if failed:
                logger.error(
                    "\n%d file(s) are not properly formatted:", len(failed))
                for f in failed:
                    logger.error("  %s", f)
                sys.exit(1)
            else:
                logger.info("All files are properly formatted.")
        else:
            logger.info("\nSuccessfully processed %d file(s).", len(files))


if __name__ == "__main__":
    main()
