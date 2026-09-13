# Documentation

This documentation is built with [MkDocs](https://www.mkdocs.org/) using the ReadTheDocs theme.
The documentation has been written with assistance of an LLM (claude-4-sonnet).

## ReadTheDocs Deployment

The documentation is automatically deployed to ReadTheDocs when changes are pushed to the main branch.

### Setup

1. **Import your repository** to [ReadTheDocs](https://readthedocs.org/):
   - Sign in to ReadTheDocs with your GitHub account
   - Click "Import a Project"
   - Select your `pyp2spec` repository

2. **Configure the project**:
   - The `.readthedocs.yaml` configuration file will be automatically detected
   - Python version is set to 3.13
   - Documentation dependencies are installed from the `docs` extra in `pyproject.toml`

3. **Documentation URL**: https://pyp2spec.readthedocs.io/

### Local Development

To build and serve the documentation locally:

```bash
# Install documentation dependencies
pip install -e .[docs]

# Serve the documentation locally
mkdocs serve

# Build the documentation
mkdocs build
```

The documentation will be available at http://127.0.0.1:8000/

### Configuration Files

- `.readthedocs.yaml`: ReadTheDocs configuration
- `mkdocs.yml`: MkDocs configuration
- `pyproject.toml`: Python project configuration with documentation dependencies
