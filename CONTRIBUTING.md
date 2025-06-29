# Contributing to Ordnung

Thank you for your interest in contributing to Git Flow Action! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in the [Issues](https://github.com/kvendingoldo/ordnung/issues) section
2. If not, create a new issue with a clear and descriptive title
3. Include as much relevant information as possible:
   - Steps to reproduce the bug
   - Expected behavior
   - Actual behavior
   - Environment details (OS, Python version, etc.)
   - Screenshots if applicable

### Suggesting Features

1. Check if the feature has already been suggested in the [Issues](https://github.com/kvendingoldo/ordnung/issues) section
2. If not, create a new issue with a clear and descriptive title
3. Provide a detailed description of the feature
4. Explain why this feature would be useful
5. Include any relevant examples or use cases

### Pull Requests

1. Fork the repository
2. Create a new branch for your changes
3. Make your changes
4. Add or update tests as needed
5. Ensure all tests pass
6. Update documentation if necessary
7. Submit a pull request

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/kvendingoldo/ordnung.git
   cd git-flow-action
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Testing

Run the test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src tests/
```

### Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints for function parameters and return values
- Write docstrings for all functions and classes
- Keep functions small and focused
- Use meaningful variable and function names

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `test`: Adding or modifying tests
- `chore`: Changes to build process or auxiliary tools

### Documentation

- Update README.md if you add new features or change existing behavior
- Add docstrings to new functions and classes
- Update examples if necessary
- Keep the documentation clear and concise

### Review Process

1. All pull requests require at least one review
2. CI checks must pass
3. Code coverage should not decrease
4. Documentation must be updated
5. Tests must be added for new features

## Getting Help

If you need help or have questions:
1. Check the [documentation](README.md)
2. Search existing [issues](https://github.com/kvendingoldo/git-flow-action/issues)
3. Create a new issue if your question hasn't been answered

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [Apache 2.0 License](LICENSE).
