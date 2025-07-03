# Quick Start

This guide will help you get started with pyp2spec quickly. We'll walk through creating your first spec file.
Make sure you have pyp2spec installed. If not, see the [Installation](installation.md) guide.

## Creating a specfile

Let's create a spec file for a simple Python package. We'll use the `click` package as an example:

```bash
pyp2spec click
```

This command will:

1. Fetch package information from PyPI
2. Generate a configuration file (`python-click.conf`)
3. Create a spec file (`python-click.spec`)

## Understanding the output

After running the command, you'll see two files in your current directory:

### Configuration file (`python-click.conf`)

This TOML file contains all the metadata extracted from PyPI:

```toml
license = "BSD-3-Clause"
archful = false
summary = "Composable command line interface toolkit"
pypi_version = "8.1.7"
pypi_name = "click"
python_name = "python-click"
url = "https://palletsprojects.com/p/click/"
source = "PyPI"
extras = []
license_files_present = true
archive_name = "click-8.1.7.tar.gz"
```

### Specfile (`python-click.spec`)

This is the RPM spec file that can be used to build the package:

```spec
Name:           python-click
Version:        8.1.7
Release:        %autorelease
Summary:        Composable command line interface toolkit

License:        BSD-3-Clause
URL:            https://palletsprojects.com/p/click/
Source:         %{pypi_source click}

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
This is package 'click' generated automatically by pyp2spec.}

%description %_description

%package -n     python3-click
Summary:        %{summary}

%description -n python3-click %_description

%prep
%autosetup -p1 -n click-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files click

%check
%pyproject_check_import

%files -n python3-click -f %{pyproject_files}

%changelog
%autochangelog
```

## Two-stage process

pyp2spec works in two stages:

1. **Configuration Generation** (`pyp2conf`): Extracts information from PyPI
2. **Spec Generation** (`conf2spec`): Creates the spec file from the configuration

You can run these stages separately:

```bash
# Stage 1: Generate configuration
pyp2conf click

# Stage 2: Generate spec file
conf2spec click.conf
```

## Next Steps

Now that you've created your first spec file, you might want to:

1. See more [Basic Examples](../examples/basic-packages.md) for different scenarios
2. Dig into the [Custom Configuration ](../examples/custom-configuration.md) for different scenarios

## Tips for Success

!!! tip "Review Generated Files"
    Always review the generated spec file before using it in production. The tool provides a good starting point, but you may need to make manual adjustments.

!!! tip "Test Building"
    Test building the RPM package with `rpmbuild` or `mock` to ensure it works correctly.

!!! tip "Fedora Guidelines"
    Familiarize yourself with the [Fedora Python Packaging Guidelines](https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/) to understand best practices. 