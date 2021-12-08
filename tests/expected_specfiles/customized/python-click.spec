Name:           python-click
Version:        7.1.2
Release:        6%{?dist}
Summary:        Simple wrapper around optparse for powerful command line utilities

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        BSD
URL:            https://github.com/mitsuhiko/click
Source0:        %{url}/archive/%{version}/click-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
click is a Python package for creating beautiful command line interfaces in a
composable way with as little amount of code as necessary. It's the "Command
Line Interface Creation Kit". It's highly configurable but comes with good
defaults out of the box.}


%description %_description

%package -n     python3-click
Summary:        %{summary}

%description -n python3-click %_description


%prep
%autosetup -p1 -n click-%{version}


%generate_buildrequires
%pyproject_buildrequires -t


%build
%pyproject_wheel


%install
%pyproject_install
# For official Fedora packages, including files with '*' +auto is not allowed
# Replace it with a list of relevant Python modules/globs and list extra files in %%files
%pyproject_save_files '*' +auto


%check
%pyproject_check_import
%tox


%files -n python3-click -f %{pyproject_files}
%doc README.rst CHANGES.rst
%license LICENSE.rst


%changelog
* Wed Jun 02 2021 Package Maintainer <package@maintainer.com> - 7.1.2-6
- Rebuilt for Python 3.10