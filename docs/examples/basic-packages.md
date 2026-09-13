# Basic examples

## Simple package example

This example demonstrates how to create a spec file for a simple Python package using pyp2spec.
We'll create a spec file for the `click` package, which is a popular Python library for creating command-line interfaces.

### Generate the specfile

Run the pyp2spec command:

```bash
pyp2spec click
```

This will create two files in your current directory:

- `python-click.conf` - Configuration file with package metadata
- `python-click.spec` - RPM spec file


### Review the specfile

```spec
Name:           python-click
Version:        8.1.7
Release:        %autorelease
# Fill in the actual package summary to submit package to Fedora
Summary:        Composable command line interface toolkit

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        BSD-3-Clause
URL:            https://github.com/pallets/click/
Source:         %{pypi_source click}

BuildArch:      noarch
BuildRequires:  python3-devel


# Fill in the actual package description to submit package to Fedora
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
# Add top-level Python module names here as arguments, you can use globs
%pyproject_save_files -l ...


%check
%pyproject_check_import


%files -n python3-click -f %{pyproject_files}


%changelog
%autochangelog

```

## Package with extras

This example demonstrates how to create a spec file for a Python package with extras.
We'll create a spec file for the `urllib3` package.

### Generate the specfile

Run the pyp2spec command:

```bash
pyp2spec urllib3
```

This will create two files in your current directory:

- `python-urllib3.conf` - Configuration file with package metadata
- `python-urllib3.spec` - RPM spec file

### Review the specfile

```
<snip>

# For official Fedora packages, review which extras should be actually packaged
# See: https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#Extras
%pyproject_extras_subpkg -n python3-urllib3 brotli,h2,socks,zstd


%prep
%autosetup -p1 -n urllib3-%{version}


%generate_buildrequires
# Keep only those extras which you actually want to package or use during tests
%pyproject_buildrequires -x brotli,h2,socks,zstd

<snip>
```

## Archful package example

This example demonstrates how to handle Python packages that contain compiled extensions.
pyp2spec can automatically detect these packages.
We'll use `numpy` as an example, which contains compiled extensions.

Generate the specfile

```bash
pyp2spec numpy
```

Review the configuration

```bash
cat python-numpy.conf
```

Notice the `archful` field:

```toml
archful = true
```

### Specfile differences

The generated spec file will differ from noarch packages:

```spec
# No `BuildArch: noarch` line
BuildRequires:  python3-devel
BuildRequires:  gcc
```
