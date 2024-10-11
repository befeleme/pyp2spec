Name:           python-numpy
Version:        1.25.2
Release:        %autorelease
# Fill in the actual package summary to submit package to Fedora
Summary:        Fundamental package for array computing in Python

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        BSD-3-Clause
URL:            https://www.numpy.org
Source:         %{pypi_source numpy}

BuildRequires:  python3-devel
BuildRequires:  gcc


# Fill in the actual package description to submit package to Fedora
%global _description %{expand:
This is package 'numpy' generated automatically by pyp2spec.}

%description %_description

%package -n     python3-numpy
Summary:        %{summary}

%description -n python3-numpy %_description


%prep
%autosetup -p1 -n numpy-%{version}


%generate_buildrequires
%pyproject_buildrequires


%build
%pyproject_wheel


%install
%pyproject_install
# For official Fedora packages, including files with '*' +auto is not allowed
# Replace it with a list of relevant Python modules/globs and list extra files in %%files
%pyproject_save_files '*' +auto


%check
%_pyproject_check_import_allow_no_modules -t


%files -n python3-numpy -f %{pyproject_files}


%changelog
%autochangelog