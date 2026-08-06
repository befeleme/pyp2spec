# Custom configuration example

This examples demonstrate how to customize generation of the specfiles.

## Create a specfile for a specific package version

Create spec files for a specific package version with `--version` or `-v`.

```bash
$ pyp2spec flask --version 3.0.2
Configuration file was saved successfully to 'python-flask.conf'
Spec file was saved successfully to 'python-flask.spec'
```

## Check if the detected license is compliant with Fedora

```bash
$ pyp2spec flask --fedora-compliant
...
Found identifiers: 'BSD-3-Clause' are good for Fedora.
...
```

## Create a specfile for a compat package

This is useful if you want to have temporarily a package with a different major version than the current in Fedora.
You can define either the major version (the latest release of that version will be chosen),
or a major.minor (the latest release of that combination will be chosen),
or a major.minor.patch release.

```bash
$ pyp2spec flask --compat 2        
Creating a compat package for version: '2'
Assuming the version found on PyPI: '2.3.3'
...
Configuration file was saved successfully to 'python-flask2.conf'
Spec file was saved successfully to 'python-flask2.spec'
```

```bash
$ pyp2spec flask --compat 2.1
Creating a compat package for version: '2.1'
Assuming the version found on PyPI: '2.1.3'
```

### Inspect the specfile

```spec
Name:           python-flask2
Version:        2.3.3
```

## Alternate Python version

Create spec files for alternate Python version with `--python-alt-version` or `-p`.

```bash
# For different Python versions
$ pyp2spec --python-alt-version 3.9 flask
python3.9-flask.conf
python3.9-flask.spec

$ pyp2spec --python-alt-version 3.11 flask
Assuming the version found on PyPI: '3.1.1'
Assuming build for Python: 3.11
Configuration file was saved successfully to 'python3.11-flask.conf'
Spec file was saved successfully to 'python3.11-flask.spec'
```

### Inspect the specfile

```spec
%global python3_pkgversion 3.11

Name:           python3.11-flask
Version:        3.1.1
```

## Declarative buildsystem (experimental)

The declarative buildsystem is a new feature available in RPM 4.20+ and pyproject-rpm-macros that allows for more streamlined spec file generation.
This feature is experimental and may change in future versions. It cannot be combined with automode.

```bash
$ pyp2spec flask --declarative-buildsystem
```

### Inspect the specfile

```spec
...
BuildSystem:    pyproject
# Replace ... with top-level Python module names as arguments, you can use globs
BuildOption(install):  -l ...
# Keep only those extras which you actually want to package or use during tests
# If you don't want to package any of them, erase the whole line
BuildOption(generate_buildrequires): -x async,dotenv
...
```
