Name:           python-urllib3_2
Version:        2.3.0
Release:        %autorelease
# Fill in the actual package summary to submit package to Fedora
Summary:        HTTP library with thread-safe connection pooling, file post, and more.

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        MIT
URL:            https://github.com/urllib3/urllib3/blob/main/CHANGES.rst
Source:         %{pypi_source urllib3}

BuildArch:      noarch
BuildRequires:  python3-devel


# Fill in the actual package description to submit package to Fedora
%global _description %{expand:
This is package 'urllib3' generated automatically by pyp2spec.}

%description %_description

%package -n     python3-urllib3_2
Summary:        %{summary}

Conflicts:      python3-urllib3
Provides:       deprecated()

%description -n python3-urllib3 %_description

# For official Fedora packages, review which extras should be actually packaged
# See: https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#Extras
%pyproject_extras_subpkg -n python3-urllib3 brotli,h2,socks,zstd


%prep
%autosetup -p1 -n urllib3-%{version}


%generate_buildrequires
# Keep only those extras which you actually want to package or use during tests
%pyproject_buildrequires -x brotli,h2,socks,zstd


%build
%pyproject_wheel


%install
%pyproject_install
# Add top-level Python module names here as arguments, you can use globs
%pyproject_save_files -l ...


%check
%pyproject_check_import


%files -n python3-urllib3_2 -f %{pyproject_files}


%changelog
%autochangelog