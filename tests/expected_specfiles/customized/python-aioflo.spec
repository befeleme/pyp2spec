Name:           python-aioflo
Version:        0.4.2
Release:        4%{?dist}
Summary:        Python library for Flo by Moen Smart Water Detectors

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        MIT
URL:            https://github.com/bachya/aioflo
Source0:        %{url}/archive/%{version}/aioflo-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
An asyncio-friendly Python library for Flo Smart Water Detectors.}

BuildRequires:  python3dist(poetry-core)
BuildRequires:  python3dist(pytest)
BuildRequires:  python3dist(aiohttp)
BuildRequires:  python3dist(aresponses)
BuildRequires:  python3dist(pytest-aiohttp)
BuildRequires:  python3dist(pytest-cov)

%description %_description

%package -n     python3-aioflo
Summary:        %{summary}

%description -n python3-aioflo %_description


%prep
%autosetup -p1 -n aioflo-%{version}


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
%pytest


%files -n python3-aioflo -f %{pyproject_files}
%doc AUTHORS.md README.md
%license LICENSE


%changelog
* Fri Jun 04 2021 Package Manager <package@manager.com> - 0.4.2-4
- Rebuilt for Python 3.10