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
BuildRequires:  python3-devel


# Fill in the actual package description to submit package to Fedora
%global _description %{expand:
{{description}}}

{% if manual_build_requires -%}
{% for br in manual_build_requires -%}
BuildRequires:  {{br}}
{% endfor -%}
{% endif %}
%description %_description

%package -n     python3-{{name}}
Summary:        %{summary}

%description -n python3-{{name}} %_description


%prep
%autosetup -p1 -n {{archive_name}}-{{pypi_version}}


%generate_buildrequires
%pyproject_buildrequires{% if extra_build_requires %} {{extra_build_requires}}{% endif %}


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

%files -n python3-{{name}} -f %{pyproject_files}
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
