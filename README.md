# pyp2spec

This project is a thought descendant of [specfile_generator](https://github.com/frenzymadness/specfile_generator).

It generates working Fedora RPM spec file for Python projects.
The produced spec files must be compliant with the current [Python Packaging Guidelines](https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/) (in effect since 2021).
It utilizes the benefits of [pyproject-rpm-macros](https://src.fedoraproject.org/rpms/pyproject-rpm-macros).

This project's maturity state is alpha.
Its API may be a subject of change.

## What it does

`pyp2spec` gathers all the necessary information from PyPI to produce a valid
Fedora spec file and stores it in the current directory alongside with
the config file used to produce the spec file.

Inside, there are two parts:
- *pyp2conf*: gathers of all the necessary information to produce a spec file and stores it in a configuration file
- *conf2spec*: produces working spec file using all the information from configuration file

## How to run

To run whatever this project offers at this point,
install package `pyp2spec` from PyPI with the command:
```
pip install pyp2spec
```
Then you can run:
```
pyp2spec <pypi_package_name>
```
or those two commands which will together produce the same result as `pyp2spec`:
```
pyp2conf <pypi_package_name>
conf2spec <config_file>
```

To see all available command-line options, run `--help` with the respective commands.

## Development

Alternatively, you can clone the project from GitHub and install
the dependencies to you virtual environment:
```
python -m pip install -r requirements.txt
```

To run the script and generate both the config and spec file, type:
```
python -m pyp2spec.pyp2spec <pypi_package_name>
```

You can run either of the tools separately to generate partial results:
```
python -m pyp2spec.pyp2conf <pypi_package_name>
python -m pyp2spec.conf2spec <config_file>
```

### Tests

To run the tests, run [tox](https://tox.wiki/en/stable/index.html):

```
tox
```

You can install `tox` from your OS repository or PyPI.
Test dependencies are defined in the project's `[test]` extra.


## Configuration file specification

Configuration data is stored in a TOML file.

### Mandatory fields

- Generated by pyp2conf

| Field  | Description | Type |
| -------- | -------- | -------- |
| pypi_name | package name as stored in PyPI  | string   |
| python_name | pypi_name prepended with `python-` | string |
| archive_name | source tarball name, stripped of version and file extension  | string |
| version | package version to create spec file for (RPM format) | string |
| pypi_version | package version string as in PyPI, '%{version}' if the same as version | string
| summary | short package summary | string |
| license | license name | string |
| url | project URL | string |
| source | %{pypi_source} macro with optional arguments (tarball URL can be used instead) | string |
| description | long package description | multiline string |
| extras | extra subpackages names | list of strings |
| archful | package contains compiled extensions, implies not using `BuildArch: noarch` and adding `BuildRequires: gcc` | bool


### Optional fields

- Not generated by pyp2conf
- Can be also added to config files generated by pyp2conf


| Field | Description | Type |
| -------- | -------- | -------- |
| test_method     | `pytest`, `tox`     | string     |
| test_top_level     | filter and test only top-level modules in %check   | bool     |
| unwanted_tests     | test names to skip with pytest     | list     |
| binary_files     | list binary files from the package     | list     |
| license_files     | list license files from the package     | list     |
| doc_files     | list doc files from the package     | list |


### Example config file generated by pyp2spec

```
description = "This is package 'aionotion' generated automatically by pyp2spec."
summary = "A simple Python 3 library for Notion Home Monitoring"
version = "2.0.3"
license = "MIT"
pypi_name = "aionotion"
pypi_version = %{version}
python_name = "python-aionotion"
url = "https://github.com/bachya/aionotion"
source = "%{pypi_source aionotion}"
archive_name = "aionotion"
extras = []
archful = false
```

### Spec file generated using the example config

```
Name:           python-aionotion
Version:        3.0.2
Release:        %autorelease
Summary:        A simple Python 3 library for Notion Home Monitoring

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        MIT
URL:            https://github.com/bachya/aionotion
Source:         %{pypi_source aionotion}

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
This is package 'aionotion' generated automatically by pyp2spec.}


%description %_description

%package -n     python3-aionotion
Summary:        %{summary}

%description -n python3-aionotion %_description


%prep
%autosetup -p1 -n aionotion-%{version}


%generate_buildrequires
%pyproject_buildrequires


%build
%pyproject_wheel


%install
%pyproject_install
# For official Fedora packages, including files with '*' +auto is not allowed
# Replace it with a list of relevant Python modules/globs and list extra files in %%files
%pyproject_save_files '*' +auto


%check
%pyproject_check_import


%files -n python3-aionotion -f %{pyproject_files}


%changelog
%autochangelog
```


## License

The code is licensed under **MIT**.

The spec file template - `template.spec` and the files generated by the tool are licensed under **MIT-0 (No Attribution)**.
