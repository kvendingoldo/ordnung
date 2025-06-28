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
- **Extensive test coverage**: Comprehensive test suite with file-based comparisons

## Installation

### Using pip
```bash
pip install -r requirements.txt
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
python -m ordnung.file_sorter data.json
python -m ordnung.file_sorter config.yaml
```

Sort a file and save to a new file:
```bash
python -m ordnung.file_sorter data.json -o sorted_data.json
python -m ordnung.file_sorter config.yaml -o sorted_config.yaml
```

### Batch Processing

Sort multiple files:
```bash
python -m ordnung.file_sorter file1.json file2.yaml file3.yml
```

Sort all JSON/YAML files in a directory:
```bash
python -m ordnung.file_sorter ./mydir --recursive
```

Use glob patterns:
```bash
python -m ordnung.file_sorter './data/**/*.json' --pattern
python -m ordnung.file_sorter './configs/*.yaml' --pattern
```

Filter with regex:
```bash
python -m ordnung.file_sorter ./mydir --regex '.*\\.ya?ml$'
python -m ordnung.file_sorter ./data --regex '.*_config\\.json$'
```

### Command Line Options

- `inputs`: Input file(s), directory(ies), or glob pattern(s) (required)
- `-o, --output`: Output file (only for single file input)
- `--indent`: Indentation for JSON files (default: 2)
- `--recursive`: Recursively search directories
- `--pattern`: Treat input as glob pattern(s)
- `--regex`: Regex to further filter files

### Examples

```bash
# Sort JSON file with 4-space indentation
python -m ordnung.file_sorter data.json --indent 4

# Sort YAML file and save to new file
python -m ordnung.file_sorter config.yaml -o sorted_config.yaml

# Sort and overwrite original file
python -m ordnung.file_sorter settings.json

# Process all JSON files in a directory recursively
python -m ordnung.file_sorter ./configs --recursive

# Use glob pattern to find files
python -m ordnung.file_sorter './**/*.json' --pattern

# Filter files with regex
python -m ordnung.file_sorter ./data --regex '.*_prod\\.ya?ml$'
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

# Run specific test categories
pytest -m "not slow"
pytest -m integration
```

### Test Structure

The test suite includes:
- **File-based tests**: 10+ tests using input/expected file pairs
- **Integration tests**: End-to-end workflow testing
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
│   ├── test_file_sorter.py
│   └── data/
│       ├── json_input*.json
│       ├── json_expected*.json
│       ├── yaml_input*.yaml
│       └── yaml_expected*.yaml
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

## Error Handling

The tool handles various error conditions:
- **File not found**: Clear error message with file path
- **Invalid JSON/YAML**: Detailed parsing error messages
- **Permission errors**: File access and write permission issues
- **Unsupported file types**: Graceful handling of unknown formats
- **Empty files**: Proper error handling for empty content

## Dependencies

- **Python 3.8+**: Modern Python features and type hints
- **PyYAML**: YAML file parsing and writing
- **Standard library**: argparse, json, pathlib, tempfile, unittest, glob, re

## License

This project is open source and available under the MIT License.
