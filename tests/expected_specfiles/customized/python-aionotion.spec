Name:           python-aionotion
Version:        2.0.3
Release:        4%{?dist}
Summary:        Python library for Notion Home Monitoring

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        MIT
URL:            https://github.com/bachya/aionotion
Source0:        %{pypi_source aionotion}

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
A asyncio-friendly library for Notion Home Monitoring devices.}


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
%pyproject_check_import -t


%files -n python3-aionotion -f %{pyproject_files}


%changelog
* Fri Jun 04 2021 Package Manager <package@manager.com> - 2.0.3-4
- Rebuilt for Python 3.10