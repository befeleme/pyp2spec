Name:           python-tomli
Version:        1.1.0
Release:        1%{?dist}
Summary:        A little TOML parser for Python

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        MIT
URL:            https://pypi.org/project/tomli/
Source0:        https://github.com/hukkin/tomli/archive/refs/tags/%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
Tomli is a Python library for parsing TOML. Tomli is fully compatible with TOML
v1.0.0.}

BuildRequires:  python3-pytest
BuildRequires:  python3-dateutil

%description %_description

%package -n     python3-tomli
Summary:        %{summary}

%description -n python3-tomli %_description


%prep
%autosetup -p1 -n tomli-%{version}


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
%pytest


%files -n python3-tomli -f %{pyproject_files}
%doc README.md CHANGELOG.md
%license LICENSE


%changelog
* Thu Jul 29 2021 Package Maintainer <package@maintainer.com> - 1.1.0-1
- Update to version 1.1.0
  - `load` can now take a binary file object
