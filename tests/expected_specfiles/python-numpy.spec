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
# Add top-level Python module names here as arguments, you can use globs
%pyproject_save_files ...


%check
%pyproject_check_import


%files -n python3-numpy -f %{pyproject_files}


%changelog
%autochangelog