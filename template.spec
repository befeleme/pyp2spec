Name:           {{python_name}}
Version:        {{version}}
Release:        {{release}}%{?dist}
Summary:        {{summary}}

License:        {{license}}
URL:            {{url}}
Source0:        {{source}}

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
{{description}}}

{% for br in manual_build_requires %}BuildRequires: {{br}}
{% endfor %}
%description %_description

%package -n     python3-{{name}}
Summary:        %{summary}

%description -n python3-{{name}} %_description


%prep
%autosetup -p1 -n {{archive_name}}-%{version}


%generate_buildrequires
%pyproject_buildrequires{% if extra_build_requires %} {{extra_build_requires}}{% endif %}


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files {{module_name}}


%check
{{test_method}}


%files -n python3-{{name}} -f %{pyproject_files}
%doc {{doc_files}}
%license {{license_files}}
{% for bf in binary_files %}%{_bindir}/{{bf}}
{% endfor %}

%changelog
* {{changelog_head}} - {{version}}-{{release}}
- {{changelog_msg}}