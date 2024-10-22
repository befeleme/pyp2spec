Name:           python-sphinx
Version:        8.1.3
Release:        %autorelease
# Fill in the actual package summary to submit package to Fedora
Summary:        Python documentation generator

# No license information obtained, it's up to the packager to fill it in
License:        ...
URL:            https://www.sphinx-doc.org/en/master/changes.html
Source:         %{pypi_source sphinx}

BuildArch:      noarch
BuildRequires:  python3-devel


# Fill in the actual package description to submit package to Fedora
%global _description %{expand:
This is package 'sphinx' generated automatically by pyp2spec.}

%description %_description

%package -n     python3-sphinx
Summary:        %{summary}

%description -n python3-sphinx %_description

# For official Fedora packages, review which extras should be actually packaged
# See: https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#Extras
%pyproject_extras_subpkg -n python3-sphinx docs,lint,test


%prep
%autosetup -p1 -n sphinx-%{version}


%generate_buildrequires
# Keep only those extras which you actually want to package or use during tests
%pyproject_buildrequires -x docs,lint,test


%build
%pyproject_wheel


%install
%pyproject_install
# Add top-level Python module names here as arguments, you can use globs
%pyproject_save_files ...


%check
%pyproject_check_import


%files -n python3-sphinx -f %{pyproject_files}


%changelog
%autochangelog