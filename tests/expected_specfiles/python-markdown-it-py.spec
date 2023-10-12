Name:           python-markdown-it-py
Version:        1.1.0
Release:        %autorelease
# Fill in the actual package summary to submit package to Fedora
Summary:        Python port of markdown-it

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        MIT
URL:            https://github.com/executablebooks/markdown-it-py
Source:         %{url}/archive/v%{version}/markdown-it-py-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel


# Fill in the actual package description to submit package to Fedora
%global _description %{expand:
Markdown parser done right. Its features: Follows the CommonMark spec for
baseline parsing. Has configurable syntax: you can add new rules and even
replace existing ones. Pluggable: Adds syntax extensions to extend the parser.
High speed & safe by default}

%description %_description

%package -n     python3-markdown-it-py
Summary:        %{summary}

%description -n python3-markdown-it-py %_description


%prep
%autosetup -p1 -n markdown-it-py-%{version}


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
%pyproject_check_import


%files -n python3-markdown-it-py -f %{pyproject_files}
%{_bindir}/markdown-it


%changelog
%autochangelog
