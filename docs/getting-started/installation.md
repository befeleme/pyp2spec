# Installation

This guide will help you install pyp2spec on your system.

## Requirements

- Python 3.9 or higher
- Linux operating system (primarily tested on Fedora)
- For development: Git

## Installation Methods

### From PyPI

The easiest way to install pyp2spec is using pip:

```bash
pip install pyp2spec
```

This will install pyp2spec and all its dependencies.

### From Fedora Repository

If you're using Fedora, you can install pyp2spec directly from the official repositories:

```bash
dnf install pyp2spec
```

### From Source

For development or to get the latest features, you can install from source:

```bash
git clone https://github.com/befeleme/pyp2spec.git
cd pyp2spec
pip install -e .
```

## Dependencies

pyp2spec depends on the following Python packages:

- `click` - Command-line interface
- `jinja2` - Template engine for spec files
- `license-expression` - License expression parsing
- `packaging` - Package metadata handling
- `requests` - HTTP requests for PyPI API
- `tomli` - TOML file reading (Python < 3.11)
- `tomli-w` - TOML file writing

These dependencies are automatically installed when you install pyp2spec.

## Next Steps

Once pyp2spec is installed, check out the [Quick Start](quick-start.md) guide to learn how to use it. 