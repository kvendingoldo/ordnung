# Ordnung

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

<!-- LOGO -->
<br />
<div align="center">
  <a>
    <img src="assets/logo3.png" alt="Logo" width="250" height="250">
  </a>
</div>

**Ordnung** is a Python utility for sorting YAML and JSON files alphabetically by keys. It supports batch processing, directory traversal, pattern matching, and is designed for both development and CI/CD workflows.

## ✨ Features

- **🔧 Automatic file type detection** - Supports `.json`, `.yaml`, and `.yml` files (including both single-document and multi-document YAML files with `---` separators)
- **📁 Batch processing** - Process multiple files, directories, or use glob patterns
- **🔄 Recursive sorting** - Sorts nested dictionaries, lists, and complex data structures
- **🎯 Pattern matching** - Filter files with glob patterns and regex
- **🚫 File exclusion** - Exclude files matching patterns (supports glob and regex)
- **✅ Check mode** - Verify formatting without rewriting files (CI-friendly)
- **🔍 Data validation** - Validate that all data structures are preserved after sorting
- **📏 Custom indentation** - Configurable indentation for both JSON and YAML
- **🔢 Array sorting** - Optionally sort arrays of objects by first key value
- **🌍 Unicode support** - Full support for international characters
- **⚡ Fast and efficient** - Optimized for large files and batch operations

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install ordnung

# Or install from source
git clone <repository-url>
cd ordnung
pip install -e .
```

### Basic Usage

```bash
# Sort a single file (overwrites original)
ordnung config.json
ordnung settings.yaml

# Sort and save to new file
ordnung input.json -o sorted.json

# Sort multiple files
ordnung file1.json file2.yaml file3.yml
```

## 📖 Usage Examples

### File Processing

Ordnung supports both single-document YAML and multi-document YAML files (with `---` separators). Each document in a multi-document YAML file will be sorted individually, and document order can be preserved or sorted using the appropriate flag.

```bash
# Sort single files
ordnung config.json
ordnung settings.yaml

# Sort multi-document YAML (all docs in file will be sorted)
ordnung multi-docs.yaml

# Sort multiple files at once
ordnung file1.json file2.yaml file3.yml

# Save to new file (only for single file input)
ordnung input.json -o sorted.json
```

### Directory Processing

```bash
# Sort all JSON/YAML files in a directory
ordnung ./configs

# Recursively process subdirectories
ordnung ./configs --recursive

# Use glob patterns
ordnung './data/**/*.json' --pattern
ordnung './configs/*.yaml' --pattern
```

### Advanced Filtering

```bash
# Filter with regex patterns
ordnung ./mydir --regex '.*\.ya?ml$'
ordnung ./data --regex '.*_prod\.json$'
ordnung ./configs --regex '.*_config\.ya?ml$'

# Combine recursive search with regex
ordnung ./data --recursive --regex '.*\.json$'
```

### File Exclusion

```bash
# Exclude files matching patterns
ordnung ./data --exclude '*.tmp' --exclude 'backup_*'
ordnung ./configs --exclude '.*\.bak$' --recursive

# Exclude with multiple patterns
ordnung ./data --exclude '*.tmp' --exclude '*.bak' --exclude 'backup_*'

# Combine exclusion with other filters
ordnung ./data --exclude '*.tmp' --regex '.*\.json$' --recursive
```

### CI/CD Integration

```bash
# Check mode: verify formatting without modifying files
ordnung ./data --check

# Use in CI pipeline (exits with error if files need formatting)
ordnung ./configs --recursive --check
```

### Data Validation

```bash
# Validate data preservation during sorting
ordnung config.json --validate
ordnung ./data --validate --recursive

# Combine validation with other options
ordnung ./configs --validate --exclude '*.tmp' --recursive

# Use validation in CI/CD pipelines
ordnung ./data --validate --check --recursive
```

### Custom Formatting

```bash
# Custom indentation
ordnung config.json --json-indent 4
ordnung settings.yaml --yaml-indent 4

# Sort arrays of objects by first key value
ordnung data.json --sort-arrays-by-first-key
```

### Debugging

```bash
# Verbose logging
ordnung config.json --log-level DEBUG

# Quiet mode
ordnung config.json --log-level ERROR
```

## 🔧 Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `inputs` | Input file(s), directory(ies), or glob pattern(s) | `config.json` |
| `-o, --output` | Output file path (single file only) | `-o sorted.json` |
| `--json-indent` | JSON indentation spaces (default: 2) | `--json-indent 4` |
| `--yaml-indent` | YAML indentation spaces (default: 2) | `--yaml-indent 4` |
| `--recursive` | Recursively search directories | `--recursive` |
| `--pattern` | Treat inputs as glob patterns | `--pattern` |
| `--regex` | Filter files with regex | `--regex '.*\.json$'` |
| `--exclude` | Exclude files matching pattern (can be used multiple times) | `--exclude '*.tmp'` |
| `--validate` | Validate that all data structures are preserved after sorting | `--validate` |
| `--check` | Check formatting without modifying | `--check` |
| `--sort-arrays-by-first-key` | Sort arrays by first key value | `--sort-arrays-by-first-key` |
| `--sort-docs-by-first-key` | For YAML files with multiple documents (--- separated), sort documents by the type and string value of the first key's value in each document, for robust and deterministic ordering. Documents with string values come before int, then float, then dict, then list, etc. For example: all docs whose first key is a string value are first, then int, then dict, then list. | `--sort-docs-by-first-key` |
| `--log-level` | Set logging level | `--log-level DEBUG` |

## 📋 Examples

### Before and After

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

### Array Sorting

**Input (with `--sort-arrays-by-first-key`):**
```json
{
  "users": [
    {"name": "Charlie", "id": 3},
    {"name": "Alice", "id": 1},
    {"name": "Bob", "id": 2}
  ]
}
```

**Output:**
```json
{
  "users": [
    {"name": "Alice", "id": 1},
    {"name": "Bob", "id": 2},
    {"name": "Charlie", "id": 3}
  ]
}
```

### Data Validation

The `--validate` option ensures that all data structures, keys, and values are preserved during sorting. This is particularly useful for critical configuration files where data integrity is paramount.

**What gets validated:**
- ✅ All dictionary keys are preserved
- ✅ All array elements are preserved (order may change)
- ✅ All nested structures are intact
- ✅ Data types remain consistent
- ✅ Values are unchanged

**Example validation output:**
```bash
$ ordnung config.json --validate
INFO: Detected file type: JSON
INFO: Loaded data from: config.json
INFO: Data sorted successfully
INFO: Validating data preservation...
INFO: Data validation passed - all structures preserved
```

**If validation fails:**
```bash
$ ordnung config.json --validate
ERROR: Data validation failed! The following issues were found:
ERROR:   Missing keys at root: ['important_key']
ERROR:   Value mismatch at settings.debug: true vs false
ERROR: Data validation failed - data structures were not preserved during sorting
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ordnung

# Run specific test categories
pytest tests/test_dedicated.py
pytest tests/test_file_sorter.py
```

## 🏗️ Development

### Project Structure

```
ordnung/
├── src/
│   └── ordnung/
│       ├── __init__.py
│       └── file_sorter.py
├── tests/
│   ├── conftest.py          # Shared test helpers
│   ├── test_file_sorter.py  # Auto-generated file-based tests
│   ├── test_dedicated.py    # Dedicated scenario tests
│   └── data/
│       ├── pass/            # Valid test files
│       └── fail/            # Invalid test files
├── pyproject.toml
└── README.md
```

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd ordnung

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Run linting
ruff check .

# Run tests
pytest
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add or update tests
5. Run the test suite (`pytest`)
6. Ensure code quality (`ruff check .`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Code Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Write comprehensive tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [PyYAML](https://pyyaml.org/) for YAML processing
- Uses [ruff](https://github.com/astral-sh/ruff) for code quality
- Inspired by the need for consistent configuration file formatting

---

**Ordnung** - Bringing order to your configuration files! 🎯
