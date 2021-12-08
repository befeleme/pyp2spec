Name:           python-boutdata
Version:        0.1.3
Release:        0.2%{?dist}
Summary:        Python package for collecting BOUT++ data

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        LGPLv3+
URL:            http://boutproject.github.io
Source0:        %{pypi_source boutdata}

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
Python interface for reading bout++ data files.}

BuildRequires:  python3dist(setuptools)
BuildRequires:  python3dist(setuptools-scm[toml]) >= 3.4
BuildRequires:  python3dist(setuptools-scm-git-archive)
BuildRequires:  python3dist(pytest)

%description %_description

%package -n     python3-boutdata
Summary:        %{summary}

%description -n python3-boutdata %_description


%prep
%autosetup -p1 -n boutdata-%{version}


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


%files -n python3-boutdata -f %{pyproject_files}
%doc README.md
%license LICENSE


%changelog
* Fri Sep 18 2020 Package Maintainer <package@maintainer.org> - 0.1.3-0.2
- Initial package.