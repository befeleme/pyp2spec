Name:           python-markdown-it-py
Version:        1.1.0
Release:        1%{?dist}
Summary:        Python port of markdown-it. Markdown parsing, done right!

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        MIT
URL:            https://github.com/executablebooks/markdown-it-py
Source0:        %{pypi_source markdown-it-py}

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
This is package 'markdown-it-py' generated automatically by pyp2spec.}


%description %_description

%package -n     python3-markdown-it-py
Summary:        %{summary}

%description -n python3-markdown-it-py %_description


%prep
%autosetup -p1 -n markdown-it-py-%{version}


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


%files -n python3-markdown-it-py -f %{pyproject_files}


%changelog
* Wed Nov 03 2021 Packager <packager@maint.com> - 1.1.0-1
- Package generated with pyp2spec