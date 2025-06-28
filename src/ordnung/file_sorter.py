#!/usr/bin/env python3
"""
File Sorter - A utility to sort YAML and JSON files.

This script takes a YAML or JSON file as input, sorts its contents,
and writes the sorted result back to the original file or a specified output file.
"""

import argparse
import difflib
import glob
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, List, Optional

import yaml

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


def sort_dict_recursively(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: sort_dict_recursively(v) for k, v in sorted(data.items())}
    if isinstance(data, list):
        if all(isinstance(item, (str, int, float, bool)) or item is None for item in data):
            return sorted(data, key=lambda x: (x is None, str(x) if x is not None else ""))
        return [sort_dict_recursively(item) for item in data]
    return data


def load_file(file_path: str, file_type: str) -> Any:
    try:
        with Path(file_path).open(encoding="utf-8") as f:
            if file_type == "json":
                return json.load(f)
            if file_type == "yaml":
                return yaml.safe_load(f)
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
                          allow_unicode=True, sort_keys=True, indent=yaml_indent)
    except Exception as err:
        raise FileSaveError(
            f"Error saving {file_type.upper()} file: {err}") from err


def file_is_formatted(input_file: str, file_type: str, json_indent: int, yaml_indent: int) -> bool:
    """
    Check if the file is already formatted (sorted and indented as specified).
    """
    data = load_file(input_file, file_type)
    sorted_data = sort_dict_recursively(data)
    with Path(input_file).open(encoding="utf-8") as f:
        original_content = f.read().strip()
    # Render sorted data to string
    if file_type == "json":
        formatted = json.dumps(
            sorted_data, indent=json_indent, ensure_ascii=False, sort_keys=True)
    else:
        formatted = yaml.dump(sorted_data, default_flow_style=False,
                              allow_unicode=True, sort_keys=True, indent=yaml_indent).strip()
    # Normalize whitespace for YAML
    return original_content == formatted


def sort_file(input_file: str, output_file: Optional[str] = None, *, json_indent: int = 2, yaml_indent: int = 2, check: bool = False) -> bool:
    if not Path(input_file).exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    file_type = detect_file_type(input_file)
    logger.info("Detected file type: %s", file_type.upper())
    data = load_file(input_file, file_type)
    logger.info("Loaded data from: %s", input_file)
    sorted_data = sort_dict_recursively(data)
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
            for match in glob.glob(p, recursive=recursive):
                match_path = Path(match)
                if (match_path.is_file() and
                    match_path.suffix.lower() in {".json", ".yaml", ".yml"} and
                        (not regex_compiled or regex_compiled.search(str(match_path)))):
                    found.add(match_path.resolve())
        elif path.is_file():
            if (path.suffix.lower() in {".json", ".yaml", ".yml"} and
                    (not regex_compiled or regex_compiled.search(str(path)))):
                found.add(path.resolve())
        elif path.is_dir():
            for ext in ("*.json", "*.yaml", "*.yml"):
                files = path.rglob(ext) if recursive else path.glob(ext)
                for f in files:
                    if (f.is_file() and
                            (not regex_compiled or regex_compiled.search(str(f)))):
                        found.add(f.resolve())
        else:
            # Try glob pattern
            for match in glob.glob(p, recursive=recursive):
                match_path = Path(match)
                if (match_path.is_file() and
                    match_path.suffix.lower() in {".json", ".yaml", ".yml"} and
                        (not regex_compiled or regex_compiled.search(str(match_path)))):
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
                      json_indent=args.json_indent, yaml_indent=args.yaml_indent, check=False)
        except Exception:
            logger.exception("Error")
            sys.exit(1)
    else:
        # Multiple files or check mode
        for f in files:
            try:
                logger.info("\nProcessing: %s", f)
                ok = sort_file(str(f), None, json_indent=args.json_indent,
                               yaml_indent=args.yaml_indent, check=args.check)
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
