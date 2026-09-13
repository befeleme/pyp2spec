# Automode

Automode is designed for automated environments where you need packages that build successfully without manual intervention (like Copr).
It applies convenient defaults that increase the chances of creating a buildable package.
Automode applies sensible defaults for fields that couldn't be automatically determined.

## Notable features
Import checks are limited to top-level modules only, reducing the chance of import failures due to missing system dependencies.

### License handling

- All found license names are validated as SPDX identifiers
- Compliance with Fedora Legal data is checked
- Warnings are issued for incorrect licenses but don't prevent spec generation
- Valid SPDX expressions are automatically combined with "AND" operator

## Enabling automode

Use the `--automode` or `-a` flag:

```bash
pyp2spec --automode package-name
pyp2spec -a package-name
```

## Limitations

!!! warning "Not for production"
    Packages generated with automode may not fully comply with Fedora packaging guidelines and should not be submitted for official review without manual review and adjustment.
