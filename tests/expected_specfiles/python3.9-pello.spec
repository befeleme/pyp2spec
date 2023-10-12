%global python3_pkgversion 3.9

Name:           python3.9-pello
Version:        1.0.4
Release:        %autorelease
# Fill in the actual package summary to submit package to Fedora
Summary:        An example Python Hello World package

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        MIT-0
URL:            https://github.com/fedora-python/Pello
Source:         %{pypi_source Pello}

BuildArch:      noarch
BuildRequires:  python%{python3_pkgversion}-devel


# Fill in the actual package description to submit package to Fedora
%global _description %{expand:
This is package 'Pello' generated automatically by pyp2spec.}

%description %_description


# For official Fedora packages, review which extras should be actually packaged
# See: https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#Extras
%pyproject_extras_subpkg -n python%{python3_pkgversion}-pello color


%prep
%autosetup -p1 -n Pello-%{version}


%generate_buildrequires
# Keep only those extras which you actually want to package or use during tests
%pyproject_buildrequires -x color


%build
%pyproject_wheel


%install
%pyproject_install
# Add top-level Python module names here as arguments, you can use globs
%pyproject_save_files ...


%check
%pyproject_check_import


%files -n python%{python3_pkgversion}-pello -f %{pyproject_files}


%changelog
%autochangelog