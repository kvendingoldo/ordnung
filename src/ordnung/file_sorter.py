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
                return yaml.load(content, Loader=NorwaySafeLoader)
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
                yaml.dump(data, f, default_flow_style=False,
                          allow_unicode=True, sort_keys=True, indent=yaml_indent, Dumper=NorwaySafeDumper)
    except Exception as err:
        raise FileSaveError(
            f"Error saving {file_type.upper()} file: {err}") from err


def sort_file(input_file: str, output_file: Optional[str] = None, *, json_indent: int = 2, yaml_indent: int = 2, check: bool = False, sort_arrays_by_first_key: bool = False) -> bool:
    if not Path(input_file).exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    file_type = detect_file_type(input_file)
    logger.info("Detected file type: %s", file_type.upper())
    data = load_file(input_file, file_type)
    logger.info("Loaded data from: %s", input_file)
    sorted_data = sort_dict_recursively(
        data, sort_arrays_by_first_key=sort_arrays_by_first_key)
    logger.info("Data sorted successfully")
    if check:
        # Check mode: compare sorted output to file content
        with Path(input_file).open(encoding="utf-8") as f:
            original_content = f.read().strip()
        if file_type == "json":
            formatted = json.dumps(
                sorted_data, indent=json_indent, ensure_ascii=False, sort_keys=True)
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


def find_files(
    paths: List[str],
    *, recursive: bool = False,
    regex: Optional[str] = None,
    pattern_mode: bool = False,
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
                ):
                    found.add(match_path.resolve())
        elif path.is_file():
            if (
                path.suffix.lower() in {".json", ".yaml", ".yml"}
                and (not regex_compiled or regex_compiled.search(str(path)))
            ):
                found.add(path.resolve())
        elif path.is_dir():
            for ext in ("*.json", "*.yaml", "*.yml"):
                files = path.rglob(ext) if recursive else path.glob(ext)
                for f in files:
                    if f.is_file() and (not regex_compiled or regex_compiled.search(str(f))):
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
                ):
                    found.add(match_path.resolve())
    return sorted(found)


def main():
    parser = argparse.ArgumentParser(
        description="Sort YAML and JSON files (single file, multiple files, directory, or pattern)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m ordnung.file_sorter file1.json file2.yaml
  python -m ordnung.file_sorter ./mydir --recursive
  python -m ordnung.file_sorter './data/**/*.json' --pattern
  python -m ordnung.file_sorter ./mydir --regex '.*\\.ya?ml$'
  python -m ordnung.file_sorter ./mydir --check  # Check mode (CI)
  python -m ordnung.file_sorter data.json --sort-arrays-by-first-key  # Sort arrays of objects by first key
        """,
    )
    parser.add_argument(
        "inputs", nargs="+",
        help="Input file(s), directory(ies), or glob pattern(s)",
    )
    parser.add_argument("-o", "--output", dest="output_file",
                        help="Output file (only for single file input)")
    parser.add_argument("--json-indent", type=int, default=2,
                        help="Indentation for JSON files (default: 2)")
    parser.add_argument("--yaml-indent", type=int, default=2,
                        help="Indentation for YAML files (default: 2)")
    parser.add_argument("--recursive", action="store_true",
                        help="Recursively search directories")
    parser.add_argument("--pattern", action="store_true",
                        help="Treat input as glob pattern(s)")
    parser.add_argument("--regex", type=str,
                        help="Regex to further filter files")
    parser.add_argument("--check", action="store_true",
                        help="Check if files are formatted (do not rewrite)")
    parser.add_argument("--sort-arrays-by-first-key", action="store_true",
                        help="Sort arrays of objects by the value of the first key in each object")
    parser.add_argument("--log-level", default="INFO",
                        help="Set log level (DEBUG, INFO, WARNING, ERROR)")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(
    ), logging.INFO), format="%(levelname)s: %(message)s")

    files = find_files(args.inputs, recursive=args.recursive,
                       regex=args.regex, pattern_mode=args.pattern)
    if not files:
        logger.error("No matching YAML/JSON files found.")
        sys.exit(1)

    failed = []
    if len(files) == 1 and args.output_file and not args.check:
        # Single file, output specified
        try:
            sort_file(str(files[0]), args.output_file,
                      json_indent=args.json_indent, yaml_indent=args.yaml_indent, check=False, sort_arrays_by_first_key=args.sort_arrays_by_first_key)
        except Exception:
            logger.exception("Error")
            sys.exit(1)
    else:
        # Multiple files or check mode
        for f in files:
            try:
                logger.info("\nProcessing: %s", f)
                ok = sort_file(str(f), None, json_indent=args.json_indent,
                               yaml_indent=args.yaml_indent, check=args.check, sort_arrays_by_first_key=args.sort_arrays_by_first_key)
                if args.check and not ok:
                    failed.append(str(f))
            except Exception:
                logger.exception("Error processing %s", f)
                if args.check:
                    failed.append(str(f))
        if args.check:
            if failed:
                logger.error("\n%d file(s) are not formatted:", len(failed))
                for f in failed:
                    logger.error("  %s", f)
                sys.exit(1)
            else:
                logger.info("All files are formatted.")
        else:
            logger.info("\nProcessed %d file(s).", len(files))


if __name__ == "__main__":
    main()
