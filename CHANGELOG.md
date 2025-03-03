# Changelog

# [0.12.0] - 2025-03-03
### Added
- Support for compat packages of various granularity (eg. '7', '7.2').
Invoke with `--compat <compat-version-string>`
- Support for pyproject declarative buildsystem, [rpm documentation](https://rpm-software-management.github.io/rpm/manual/buildsystem.html), [pyproject-rpm-macros documentation](https://src.fedoraproject.org/rpms/pyproject-rpm-macros)
  - section 'Provisional: Declarative Buildsystem (RPM 4.20+)'.

### Changed
- Package extras are now primarily read from `provides_extra`, only after that's empty from `requires_dist`
- Updated the list of Trove License Classifiers


# [0.11.1] - 2024-11-21
### Changed
- Bring back the processing of the legacy sdist filenames (removed in v0.11.0).


# [0.11.0] - 2024-10-22
### Added
- For packages that publish METADATA with `License-File` field on PyPI,
the generated spec files contain a flag `%pyproject_save_files -l`
which asserts the presence of license files in the distribution during the RPM build

### Changed
- Implemented PEP 625: only the standardized sdist filenames are now supported


# [0.10.0] - 2024-10-10
### Added
- CLI `--automode`, `-a` to create buildable spec files (suitable for automated
environments)

### Changed
- In the default mode of pyp2spec create a spec file that requires a human input
The top-level modules cannot be easily detected, hence `%pyproject_save_files`
has to be filled in by a packager
- Continue with creating the spec files even if the license is not detected,
leave the field blank to fill in by the packager

### Removed
- Many CLI options and manual config entries. The tool now only takes care of what it can detect from the package data.


# [0.9.0] - 2024-04-11
### Added
- Added a possibility to create spec files for specific Python versions
Use a new command-line option `-p, --python-alt-version` to set it.


# [0.8.0] - 2023-10-11
### Added
- Automatically detect whether a package is archful or not based on a wheel name.
If so, `BuildArch: noarch` is not used in the resulting spec file.
If so, `BuildRequires: gcc` is automatically added to the resulting spec file.
- Automatically detect the package extras, provided that an extra contains at least one additional requirement
The detected extras are declared as RPM subpackages and required in the build time.

### Changed
- Use project version JSON API available at PyPI to obtain package metadata.
This ensures all the fields are relevant for the requested package version

### Removed
- CLI `--archful` switch - it's detected automatically now
- `manual_build_requires` config option
- `extra_build_requires` config option
- `extra_tox_env` config option
- support for Python 3.8


# [0.7.0] - 2023-05-03
### Changed
- rpmautospec macros (`%autochangelog` and `%autorelease`) are now used to populate the respective
fields in the generated specfile. The CLI options for defining custom values have been removed
- Convert the Python classifiers to Fedora SPDX expressions (where possible, based on [PEP 639](https://peps.python.org/pep-0639/))
- When `--fedora-compliant` option is set, a check of the converted license expressions is performed
to determine whether the license is allowed in Fedora. Data is provided by the [Fedora Legal team](https://gitlab.com/fedora/legal/fedora-license-data/)
- tomllib library is used to read toml files from Python 3.11 on

### Fixed
- pyp2spec quits when a package is not found on PyPI


# [0.6.1] - 2022-08-01
### Fixed
- Include LICENSE-MIT-0 in the sdist and fix license metadata


# [0.6.0] - 2022-08-01
### Changed
- template.spec and the files created by pyp2spec are relicensed under MIT-0 (No attribution) license
- PyPI package names are normalized according to PEP 503 to better conform with [Library naming guidelines](https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#_naming)
- "Initial package" is the new default changelog message, which better reflects the needs of packagers


# [0.5.0] - 2022-06-15
### Changed
- Clearly state in version that project is in the alpha maturity phase,
its API may be subject of change

# [0.4.0] - 2022-05-23
### Added
- It's possible to declare archful package via CLI (`--archful, -a`) -
the generated spec file will not contain `BuildArch: noarch` line
- Package version compatible with PEP 440 is now converted to RPM scheme,
version not following the specification remains unchanged.
For that, a modified part of [pyreq2rpm](https://github.com/gordonmessmer/pyreq2rpm/blob/master/pyreq2rpm/pyreq2rpm.py) is used

### Changed
- Requirement to generate the runtime requirements is no longer passed as an `-r` flag,
this was made the default option as of pyproject-rpm-macros 0-53
- Sources are no longer enumerated as per [this change](https://pagure.io/packaging-committee/pull-request/1157) in Fedora's Packaging Guidelines

### Fixed
- CLI `--spec-output` option has got a short version `-o`. `-s` is valid for `--summary`


## [0.3.3] - 2022-01-11
### Fixed
- Prevent creating spec file without summary (fill in placeholder `...`)
- Prevent creating spec file with multiline summary value (fill in placeholder `...`)
- Don't create a spec file when the upstream `license` field contains the whole license text instead of the keyword - error and end the program.
- Add a comment in the generated spec file that the `description` field should be filled in by the packager
- Created spec files now contain a newline at the end of file


## [0.3.2] - 2021-12-10
### Fixed
- If no `project_urls` are present in the package data, fall back to `package_url`
which always lists the PyPI package URL


## [0.3.1] - 2021-12-09
### Fixed
- When sdist is in `zip` format, it %{pypi_source} is now correctly called with all arguments: name, version and format


## [0.3.0] - 2021-12-08
### Added
- `zip` is recognized as a valid sdist format and used to create source macro
- Description lines are now wrapped at 79 characters, so they don't annoy rpmlint
- `MANIFEST.in` to include tests in sdist

### Fixed
- Cassettes were reloaded so that tests don't send real HTTP requests
- 'OSI Approved' License classifier is ignored now, it's a top-level category
that doesn't bring any meaningful information


## [0.2.0] - 2021-11-29
### Added
- Explicit comment in template.spec that "'*' +auto" is not allowed in Fedora
- Command-line option `--top-level` to filter only top-level modules during the check phase

### Changed
- Proprietary licenses are declared as "BAD" for Fedora, not "UNKNOWN"
- Minor README corrections


## [0.1.0] - 2021-11-19
### Added
- pyp2spec: First published version
