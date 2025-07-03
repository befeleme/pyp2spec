# Development Setup

This guide helps you set up a development environment for contributing to pyp2spec.

## Prerequisites

- Python 3.9 or higher
- Git
- Linux environment (preferably Fedora)

## Setting Up the Development Environment

### 1. Clone the Repository

```bash
git clone https://github.com/befeleme/pyp2spec.git
cd pyp2spec
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### 4. Install Development Dependencies

```bash
pip install -e ".[test,docs]"
```

## Running Tests

Use tox to run the test suite:

```bash
tox
```

Or run tests directly with pytest:

```bash
pytest
```

## Code Style

The project uses ruff for linting. Run it with:

```bash
ruff check pyp2spec/
```

## Documentation

### Building Documentation

```bash
pip install -e ".[docs]"
mkdocs serve
```

The documentation will be available at `http://localhost:8000`.

### Making Documentation Changes

1. Edit files in the `docs/` directory
2. Preview changes with `mkdocs serve`
3. Build the final documentation with `mkdocs build`

## Making Changes

1. Create a new branch for your feature or fix
2. Make your changes
3. Add tests for new functionality
4. Update documentation if needed
5. Run tests to ensure everything works
6. Submit a pull request

## Debugging

To debug pyp2spec during development:

```bash
python -m pyp2spec.pyp2spec package-name

# Or run individual components
python -m pyp2spec.pyp2conf package-name
python -m pyp2spec.conf2spec package-name.conf
```
