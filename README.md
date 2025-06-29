# File Sorter (Ordnung)

A Python utility for sorting YAML and JSON files with support for batch processing, directory traversal, and pattern matching.

## Features

- **Automatic file type detection**: Supports both YAML (.yaml, .yml) and JSON (.json) files
- **Recursive sorting**: Sorts nested dictionaries, lists, and complex data structures
- **Batch processing**: Process multiple files, directories, or use glob patterns
- **Flexible output**: Can overwrite original files or save to new files
- **Pattern matching**: Support for glob patterns and regex filtering
- **Comprehensive error handling**: Graceful handling of invalid files and edge cases
- **Unicode support**: Full support for international characters
- **Sort arrays by first key**: Optionally sort arrays of objects by the value of their first key
- **Check mode**: Verify formatting without rewriting files (CI-friendly)
- **Extensive test coverage**: Comprehensive test suite with file-based and dedicated scenario tests

## Installation

### Using pip
```bash
pip install ordnung
```

### From source
```bash
git clone <repository-url>
cd ordnung
pip install -e .
```

### Using uv (recommended)
```bash
uv sync
```

### Using Docker
```bash
docker build -t ordnung .
```

## Usage

### Basic Usage

Sort a single file and overwrite it:
```bash
ordnung data.json
ordnung config.yaml
```

Sort a file and save to a new file:
```bash
ordnung data.json -o sorted_data.json
ordnung config.yaml -o sorted_config.yaml
```

### Batch Processing

Sort multiple files:
```bash
ordnung file1.json file2.yaml file3.yml
```

Sort all JSON/YAML files in a directory:
```bash
ordnung ./mydir --recursive
```

Use glob patterns:
```bash
ordnung './data/**/*.json' --pattern
ordnung './configs/*.yaml' --pattern
```

Filter with regex:
```bash
ordnung ./mydir --regex '.*\.ya?ml$'
ordnung ./data --regex '.*_config\.json$'
```

### Command Line Options

- `inputs`: Input file(s), directory(ies), or glob pattern(s) (required)
- `-o, --output`: Output file (only for single file input)
- `--json-indent`: Indentation for JSON files (default: 2)
- `--yaml-indent`: Indentation for YAML files (default: 2)
- `--recursive`: Recursively search directories
- `--pattern`: Treat input as glob pattern(s)
- `--regex`: Regex to further filter files
- `--check`: Check if files are formatted (do not rewrite)
- `--sort-arrays-by-first-key`: Sort arrays of objects by the value of the first key in each object

### Examples

```bash
# Sort JSON file with 4-space indentation
ordnung data.json --json-indent 4

# Sort YAML file and save to new file
ordnung config.yaml -o sorted_config.yaml

# Sort and overwrite original file
ordnung settings.json

# Process all JSON files in a directory recursively
ordnung ./configs --recursive

# Use glob pattern to find files
ordnung './**/*.json' --pattern

# Filter files with regex
ordnung ./data --regex '.*_prod\.ya?ml$'

# Check mode (CI): verify formatting without rewriting
ordnung ./data --check
```

### Alternative Usage (Module Execution)

You can also run the tool as a Python module:
```bash
python -m ordnung.file_sorter data.json
python -m ordnung.file_sorter ./mydir --recursive
```

## How It Works

### File Type Detection

The tool detects file types in this order:
1. **File extension**: `.json`, `.yaml`, `.yml`
2. **Content analysis**: Examines file content for JSON/YAML patterns

### Sorting Algorithm

- **Dictionaries**: Keys are sorted alphabetically
- **Lists**:
  - Primitive values (strings, numbers, booleans) are sorted
  - Arrays of objects can be sorted by the value of their first key (optional)
  - Complex objects preserve order but sort their internal structure
- **Nested structures**: Recursively sorted at all levels
- **Mixed types**: Handles combinations of dictionaries, lists, and primitives

### Example Transformation

**Input JSON:**
```json
{
  "zebra": "striped animal",
  "apple": "red fruit",
  "settings": {
    "theme": "dark",
    "language": "en"
  }
}
```

**Output JSON:**
```json
{
  "apple": "red fruit",
  "settings": {
    "language": "en",
    "theme": "dark"
  },
  "zebra": "striped animal"
}
```

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ordnung

# Run dedicated scenario tests
pytest tests/test_dedicated.py

# Run file-based auto-generated tests
pytest tests/test_file_sorter.py
```

### Test Structure

The test suite includes:
- **File-based tests**: Auto-generated for each input/expected file pair in `tests/data/pass` and `tests/data/fail`
- **Dedicated scenario tests**: In `tests/test_dedicated.py` for batch, check mode, regex, pattern, indentation, and more
- **Shared helpers**: Common test helpers (e.g., `compare_json_files`, `compare_yaml_files`) are in `tests/conftest.py`
- **Error handling**: Invalid files, missing files, edge cases
- **Batch processing**: Directory and pattern matching tests

### Using Docker for Testing

```bash
# Build and run tests
docker build -t ordnung-test .
docker run --rm ordnung-test

# Run tests with volume mount for development
docker run --rm -v $(pwd):/app ordnung-test pytest
```

## Development

### Project Structure

```
ordnung/
├── src/
│   └── ordnung/
│       ├── __init__.py
│       └── file_sorter.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py  # Shared test helpers
│   ├── test_file_sorter.py  # Auto-generated file-based tests
│   ├── test_dedicated.py    # Dedicated scenario tests
│   └── data/
│       ├── pass/
│       ├── fail/
│       └── ...
├── requirements.txt
├── pyproject.toml
├── pytest.ini
├── Dockerfile
└── README.md
```

### Code Quality

```bash
# Lint with ruff
ruff check src/ tests/

# Format code
ruff format src/ tests/

# Type checking (if mypy is configured)
mypy src/
```

### Adding New Tests

1. Create input file in `tests/data/` (e.g., `json_input6.json`)
2. Create expected output file (e.g., `json_expected6.json`)
3. Add test case to `test_file_sorter_file_based` parametrize decorator

## Contributing

Contributions are welcome! Please:
- Follow the code style and naming conventions
- Add or update tests for new features or bugfixes
- Use the shared helpers in `tests/conftest.py` for consistency
- Run `pytest` and ensure all tests pass before submitting a PR

---

For questions or issues, open an issue or pull request on GitHub.

## Dependencies

- **Python 3.8+**: Modern Python features and type hints
- **PyYAML**: YAML file parsing and writing
- **Standard library**: argparse, json, pathlib, tempfile, unittest, glob, re

## License

This project is open source and available under the MIT License.
