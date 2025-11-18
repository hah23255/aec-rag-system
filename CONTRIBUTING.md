# Contributing to AEC RAG System

Thank you for your interest in contributing to the AEC RAG System! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/hah23255/aec-rag-system/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Code samples or error messages

### Suggesting Features

1. Check existing feature requests
2. Create a new issue with:
   - Clear use case description
   - Proposed solution
   - Alternative approaches considered
   - Impact on existing functionality

### Pull Requests

1. **Fork and Clone**
   ```bash
   git clone https://github.com/hah23255/aec-rag-system.git
   cd aec-rag-system
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Setup Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # if exists
   pre-commit install
   ```

4. **Make Changes**
   - Follow coding standards (see below)
   - Add tests for new features
   - Update documentation as needed

5. **Test Your Changes**
   ```bash
   pytest tests/ -v --cov
   black src/ tests/
   ruff check src/ tests/
   mypy src/
   ```

6. **Commit**
   - Use conventional commits format:
     ```
     feat: add CAD layer extraction
     fix: resolve PDF parsing memory leak
     docs: update API documentation
     test: add GraphRAG integration tests
     ```

7. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   - Open PR on GitHub
   - Fill out the PR template
   - Link related issues

## Development Standards

### Code Style

- **Python Version:** 3.9+
- **Formatter:** Black (100 character line length)
- **Linter:** Ruff
- **Type Hints:** Required for all functions
- **Docstrings:** Google style for all public functions/classes

Example:
```python
def process_document(file_path: str, max_pages: int = 100) -> dict[str, Any]:
    """Process a document and extract structured data.
    
    Args:
        file_path: Path to the document file
        max_pages: Maximum number of pages to process
        
    Returns:
        Dictionary containing extracted data and metadata
        
    Raises:
        FileNotFoundError: If file_path does not exist
        ValueError: If file format is not supported
    """
    pass
```

### Testing

- **Framework:** pytest
- **Coverage:** Maintain >80% coverage
- **Types:**
  - Unit tests: `tests/unit/`
  - Integration tests: `tests/integration/`
  - Fixtures: `tests/fixtures/`

### File Naming

- **Python files:** `lowercase_with_underscores.py`
- **Test files:** `test_module_name.py`
- **Config files:** `kebab-case.yaml`

### Directory Structure (FSH 3.0)

- `src/` - Source code
- `tests/` - Test suite
- `docs/` - Documentation
- `config/` - Configuration files
- `scripts/` - Utility scripts
- `deployment/` - Deployment configs

## Review Process

1. **Automated Checks**
   - All CI/CD tests must pass
   - Code coverage must not decrease
   - Linting must pass

2. **Code Review**
   - At least one maintainer approval required
   - Address all review comments
   - Keep PR scope focused

3. **Merge**
   - Squash and merge for feature branches
   - Rebase for hotfixes

## Development Workflow

### Local Development

```bash
# Start services
docker-compose up -d

# Run API in development mode
uvicorn src.api.main:app --reload

# Run tests
pytest tests/ -v

# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Questions?

- Open a [Discussion](https://github.com/hah23255/aec-rag-system/discussions)
- Join our community chat (if available)
- Email: your.email@example.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
