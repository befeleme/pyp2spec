Name:           python-jupyter-packaging
Version:        0.10.4
Release:        1%{?dist}
Summary:        Jupyter Packaging Utilities.

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        BSD
URL:            http://jupyter.org
Source0:        %{pypi_source jupyter_packaging}

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
This is package 'jupyter-packaging' generated automatically by pyp2spec.}


%description %_description

%package -n     python3-jupyter-packaging
Summary:        %{summary}

%description -n python3-jupyter-packaging %_description


%prep
%autosetup -p1 -n jupyter_packaging-%{version}


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


%files -n python3-jupyter-packaging -f %{pyproject_files}


%changelog
* Wed Nov 03 2021 Packager <packager@maint.com> - 0.10.4-1
- Package generated with pyp2spec