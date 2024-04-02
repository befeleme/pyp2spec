{% if python_version %}
%global python3_pkgversion {{ python_version }}
%global __python3 /usr/bin/python3.X

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
{% if python_version %}
BuildRequires:  python%{python3_pkgversion}-devel
{% else -%}
BuildRequires:  python3-devel
{% endif -%}
{% for br in additional_build_requires -%}
BuildRequires:  {{br}}
{% endfor %}

# Fill in the actual package description to submit package to Fedora
%global _description %{expand:
{{description}}}

%description %_description
{% if python_version %}
%package -n     python%{python3_pkgversion}-{{name}}
{% else %}
%package -n     python3-{{name}}
{% endif -%}
Summary:        %{summary}
{% if python_version %}
%description -n python%{python3_pkgversion}-{{name}} %_description
{% else %}
%description -n python3-{{name}} %_description
{% endif -%}
{% if extras %}
# For official Fedora packages, review which extras should be actually packaged
# See: https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#Extras
{%- if python_version %}
%pyproject_extras_subpkg -n python%{python3_pkgversion}-{{name}} {{extras}}
{% else %}
%pyproject_extras_subpkg -n python3-{{name}} {{extras}}
{% endif -%}
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
{% if python_version %}
%files -n python%{python3_pkgversion}-{{name}} -f %{pyproject_files}
{% else %}
%files -n python3-{{name}} -f %{pyproject_files}
{% endif -%}
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
