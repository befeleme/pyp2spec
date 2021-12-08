# Changelog

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
