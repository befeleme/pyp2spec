Name:           python-aionotion
Version:        2.0.3
Release:        1%{?dist}
Summary:        A simple Python 3 library for Notion Home Monitoring

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        MIT
URL:            https://github.com/bachya/aionotion
Source0:        %{pypi_source aionotion}

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
This is package 'aionotion' generated automatically by pyp2spec.}


%description %_description

%package -n     python3-aionotion
Summary:        %{summary}

%description -n python3-aionotion %_description


%prep
%autosetup -p1 -n aionotion-%{version}


%generate_buildrequires
%pyproject_buildrequires -r


%build
%pyproject_wheel


%install
%pyproject_install
# For official Fedora packages, including files with '*' +auto is not allowed
# Replace it with a list of relevant Python modules/globs and list extra files in %%files
%pyproject_save_files '*' +auto


%check
%pyproject_check_import


%files -n python3-aionotion -f %{pyproject_files}


%changelog
* Wed Nov 03 2021 Packager <packager@maint.com> - 2.0.3-1
- Package generated with pyp2spec