Name:           python-local-test
Version:        0.12.2
Release:        %autorelease
# Fill in the actual package summary to submit package to Fedora
Summary:        Test package

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        MIT AND MIT-0
URL:            ...
# Replace ... with the actual URL/path to the source archive
Source:         ...

BuildArch:      noarch
BuildRequires:  python3-devel


# Fill in the actual package description to submit package to Fedora
%global _description %{expand:
This is package 'local-test' generated automatically by pyp2spec.}

%description %_description

%package -n     python3-local-test
Summary:        %{summary}

%description -n python3-local-test %_description

# For official Fedora packages, review which extras should be actually packaged
# See: https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#Extras
%pyproject_extras_subpkg -n python3-local-test test


%prep
# Replace ... with the actual archive name
%autosetup -p1 -n ...-%{version}


%generate_buildrequires
# Keep only those extras which you actually want to package or use during tests
%pyproject_buildrequires -x test


%build
%pyproject_wheel


%install
%pyproject_install
# Add top-level Python module names here as arguments, you can use globs
%pyproject_save_files -l ...


%check
%pyproject_check_import


%files -n python3-local-test -f %{pyproject_files}


%changelog
%autochangelog