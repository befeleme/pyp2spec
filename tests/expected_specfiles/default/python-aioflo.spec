Name:           python-aioflo
Version:        0.4.2
Release:        1%{?dist}
Summary:        A Python3, async-friendly library for Flo by Moen Smart Water Detectors

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        MIT
URL:            https://github.com/bachya/aioflo
Source0:        %{pypi_source aioflo}

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
This is package 'aioflo' generated automatically by pyp2spec.}


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


%files -n python3-aioflo -f %{pyproject_files}


%changelog
* Wed Nov 03 2021 Packager <packager@maint.com> - 0.4.2-1
- Package generated with pyp2spec