Name:           python-sphinx
Version:        7.2.6
Release:        %autorelease
Summary:        Python documentation generator

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        fake-license
URL:            https://www.sphinx-doc.org/
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
# For official Fedora packages, including files with '*' +auto is not allowed
# Replace it with a list of relevant Python modules/globs and list extra files in %%files
%pyproject_save_files '*' +auto


%check
%pyproject_check_import


%files -n python3-sphinx -f %{pyproject_files}


%changelog
%autochangelog