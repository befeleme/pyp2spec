Name:           python-click
Version:        8.1.7
Release:        %autorelease
# Fill in the actual package summary to submit package to Fedora
Summary:        Composable command line interface toolkit

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        BSD-3-Clause
URL:            https://github.com/pallets/click/
Source:         %{pypi_source click}

BuildArch:      noarch
BuildRequires:  python3-devel


# Fill in the actual package description to submit package to Fedora
%global _description %{expand:
This is package 'click' generated automatically by pyp2spec.}

%description %_description

%package -n     python3-click
Summary:        %{summary}

%description -n python3-click %_description


%prep
%autosetup -p1 -n click-%{version}


%generate_buildrequires
%pyproject_buildrequires


%build
%pyproject_wheel


%install
%pyproject_install
# Automatically extracted from wheel
%pyproject_save_files -l click


%check
%pyproject_check_import


%files -n python3-click -f %{pyproject_files}


%changelog
%autochangelog
