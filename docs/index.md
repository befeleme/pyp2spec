# pyp2spec documentation

Welcome to the documentation for **pyp2spec**, a tool for generating valid Fedora RPM spec files from Python packages on PyPI.

## What is pyp2spec?

`pyp2spec` is a command-line tool that helps Fedora package maintainers by automatically generating RPM spec files from Python packages available on PyPI. It's designed to comply with the current [Python Packaging Guidelines](https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/) and utilizes the benefits of [pyproject-rpm-macros](https://src.fedoraproject.org/rpms/pyproject-rpm-macros).

## Key Features

- **Automatic spec file generation**: Creates working Fedora RPM spec files with minimal manual input
- **PyPI integration**: Fetches package metadata directly from PyPI
- **Compliance**: Follows current Fedora Python Packaging Guidelines
- **Flexible operation**: Can work in standard mode or automode for different use cases
- **Two-stage process**: Separates configuration generation from spec file creation for better control

!!! warning "This is alpha software"
    Its API may be subject to change. Always review and test the generated files before using them in production.

## Quick Start

Install pyp2spec:

```bash
pip install pyp2spec
```

Generate a spec file:

```bash
pyp2spec <package_name>
```

For example:

```bash
pyp2spec click
```

This will create both a configuration file and a spec file in your current directory.

## How It Works

`pyp2spec` consists of two main components:

1. **pyp2conf**: Gathers all necessary information from PyPI and stores it in a configuration file
2. **conf2spec**: Produces a working spec file using the information from the configuration file

You can use these tools separately or together via the main `pyp2spec` command.

## Operation Modes

### Standard Mode

The default mode generates spec files with all detected information, but may include placeholders for fields that couldn't be determined automatically. This ensures accuracy but may require manual completion.

### Automode

Activated with `--automode` or `-a`, this mode applies convenient defaults to increase the chance of creating a buildable package. It's designed for automated environments but the generated spec files may not fully comply with all Fedora packaging requirements.

### Declarative Buildsystem (Experimental)

Available with `--declarative-buildsystem`, this mode uses the new declarative buildsystem feature of RPM 4.20+ and pyproject-rpm-macros.


## Getting Help

- Browse the [Examples](examples/basic-packages.md) for common use cases
- Visit the [GitHub repository](https://github.com/befeleme/pyp2spec) for issues and contributions

## Navigation

### Getting Started

Install pyp2spec and learn the basics

- [Installation](getting-started/installation.md)
- [Quick Start](getting-started/quick-start.md)

### Examples

See pyp2spec in action with real-world examples

- [Basic Examples](examples/basic-packages.md)
- [Custom Configuration](examples/custom-configuration.md)
- [Automode](examples/automode.md)

### Contributing

- [Development Setup](contributing/development-setup.md)

### Other

- [Changelog](changelog.md) 