{% if python_alt_version -%}
%global python3_pkgversion {{ python_alt_version }}

{% endif -%}
Name:           {{python_name}}
Version:        {{version}}
Release:        %autorelease
# Fill in the actual package summary to submit package to Fedora
Summary:        {{summary}}

{{ license_notice }}
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
{% if automode -%}
# For official Fedora packages, including files with '*' +auto is not allowed
# Replace it with a list of relevant Python modules/globs and list extra files in %%files
%pyproject_save_files '*' +auto
{%- else -%}
# Add top-level Python module names here as arguments, you can use globs
%pyproject_save_files ...
{%- endif %}


%check
{% if automode -%}
%_pyproject_check_import_allow_no_modules -t
{%- else -%}
%pyproject_check_import
{%- endif %}


%files -n python{{python3_pkgversion}}-{{name}} -f %{pyproject_files}


%changelog
%autochangelog
