Name:           python-pytest7
Version:        7.4.4
Release:        %autorelease
# Fill in the actual package summary to submit package to Fedora
Summary:        pytest: simple powerful testing with Python

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        MIT
URL:            https://github.com/pytest-dev/pytest
Source:         %{pypi_source pytest}

BuildArch:      noarch
BuildRequires:  python3-devel


# Fill in the actual package description to submit package to Fedora
%global _description %{expand:
This is package 'pytest' generated automatically by pyp2spec.}

%description %_description

%package -n     python3-pytest7
Summary:        %{summary}

Conflicts:      python3-pytest
Provides:       deprecated()

%description -n python3-pytest %_description

# For official Fedora packages, review which extras should be actually packaged
# See: https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#Extras
%pyproject_extras_subpkg -n python3-pytest testing


%prep
%autosetup -p1 -n pytest-%{version}


%generate_buildrequires
# Keep only those extras which you actually want to package or use during tests
%pyproject_buildrequires -x testing


%build
%pyproject_wheel


%install
%pyproject_install
# Add top-level Python module names here as arguments, you can use globs
%pyproject_save_files -l ...


%check
%pyproject_check_import


%files -n python3-pytest7 -f %{pyproject_files}


%changelog
%autochangelog