# pyp2spec

This project is a thought descendant of [specfile_generator](https://github.com/frenzymadness/specfile_generator).

It aims to generate working Fedora RPM spec file for Python projects.
The produced spec files must be compliant with the current [Python Packaging Guidelines](https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/) (in effect since 2021).
It utilizes the benefits of [pyproject-rpm-macros](https://src.fedoraproject.org/rpms/pyproject-rpm-macros).

It is under development.

## What it will do

The project will consist of two parts:
- *pyp2conf*: gathers of all the necessary information to produce a spec file and stores it in a configuration file - **not available yet**
- *conf2spec*: produces working spec file using all the information from configuration file - **a limited set of functionalities is available**

## Configuration file specification

Configuration data is stored in a TOML file.

TBD

## How to run

To run whatever this project offers at this point, install to your virtual environment the dependencies from `requirements.txt`:

```
python -m pip install -r requirements.txt
```

Until the configuration file specification is set, you can use the test files to run the script:
```
python conf2spec.py -f tests/pyp2spec_click/pyp2spec_click.conf
```

### Tests

To run the tests, install pytest & run it:

```
python -m pip install pytest
python -m pytest
```
