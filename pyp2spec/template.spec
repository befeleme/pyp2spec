{% if python_alt_version -%}
%global python3_pkgversion {{ python_alt_version }}

{% endif -%}
Name:           {{python_name}}
Version:        {{version}}
Release:        %autorelease
Summary:        {{summary}}

# Check if the automatically generated License and its spelling is correct for Fedora
# https://docs.fedoraproject.org/en-US/packaging-guidelines/LicensingGuidelines/
License:        {{license}}
URL:            {{url}}
Source:         {{source}}
{% if not archful %}
BuildArch:      noarch
{%- endif %}
BuildRequires:  python{{python3_pkgversion}}-devel
{% for br in additional_build_requires -%}
BuildRequires:  {{br}}
{% endfor %}

# Fill in the actual package description to submit package to Fedora
%global _description %{expand:
{{description}}}

%description %_description

{% if not python_alt_version -%}
%package -n     python{{python3_pkgversion}}-{{name}}
Summary:        %{summary}

%description -n python{{python3_pkgversion}}-{{name}} %_description
{% endif -%}

{% if extras %}
# For official Fedora packages, review which extras should be actually packaged
# See: https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#Extras
%pyproject_extras_subpkg -n python{{python3_pkgversion}}-{{name}} {{extras}}
{% endif %}

%prep
%autosetup -p1 -n {{archive_name}}-{{pypi_version}}


%generate_buildrequires
{% if extras -%}
# Keep only those extras which you actually want to package or use during tests
{% endif -%}
%pyproject_buildrequires{% if extras %} -x {{extras}}{% endif %}


%build
%pyproject_wheel


%install
%pyproject_install
# For official Fedora packages, including files with '*' +auto is not allowed
# Replace it with a list of relevant Python modules/globs and list extra files in %%files
%pyproject_save_files '*' +auto


%check
%pyproject_check_import{% if test_top_level %} -t{% endif %}
{% if test_method -%}
{{test_method}}
{% endif %}

%files -n python{{python3_pkgversion}}-{{name}} -f %{pyproject_files}
{% if doc_files -%}
%doc {{doc_files}}
{% endif -%}
{% if license_files -%}
%license {{license_files}}
{% endif -%}
{% if binary_files -%}
{% for bf in binary_files -%}
%{_bindir}/{{bf}}
{% endfor -%}
{% endif %}

%changelog
%autochangelog
