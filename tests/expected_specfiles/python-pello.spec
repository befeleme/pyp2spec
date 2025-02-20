Name:           python-pello
Version:        1.0.4
Release:        %autorelease
# Fill in the actual package summary to submit package to Fedora
Summary:        An example Python Hello World package

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        MIT-0
URL:            https://github.com/fedora-python/Pello
Source:         %{pypi_source Pello}

BuildSystem:    pyproject
# Replace ... with top-level Python module names as arguments, you can use globs
BuildOption(install):  -l ...
# Keep only those extras which you actually want to package or use during tests
# If you don't want to package any of them, erase the whole line
BuildOption(generate_buildrequires): -x color

BuildArch:      noarch
BuildRequires:  python3-devel


# Fill in the actual package description to submit package to Fedora
%global _description %{expand:
This is package 'pello' generated automatically by pyp2spec.}

%description %_description

%package -n     python3-pello
Summary:        %{summary}

%description -n python3-pello %_description

# For official Fedora packages, review which extras should be actually packaged
# See: https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#Extras
%pyproject_extras_subpkg -n python3-pello color


%files -n python3-pello -f %{pyproject_files}


%changelog
%autochangelog