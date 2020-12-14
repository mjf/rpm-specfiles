# RPM specfile for Promscale Postgres extension
# Copyright (C) 2020 Matous Jan Fialka, <mjf@mjf.cz>
# Released under the terms of the "MIT License"

Name         : promscale_extension
Version      : 0.1.1
Release      : 1%{?dist}
Group        : PostgreSQL Database Server 12 PGDG
License      : Timescale License
Source       : https://github.com/timescale/%{name}/archive/%{version}.tar.gz#/%{name}-%{version}.tgz
URL          : https://github.com/timescale/%{name}/promscale_extension
Summary      : Promscale Postgres extension
BuildRequires: postgresql12-devel
BuildRequires: gcc
BuildRequires: llvm
BuildRequires: make
BuildRequires: rust
BuildRequires: cargo

%description
Promscale Postgres extension contains support functions to improve the
performance of Promscale.  While Promscale will run without it, adding this
extension will cause it to perform better.

%define debug_package %{nil}

%undefine __brp_mangle_shebangs
%undefine __brp_ldconfig

%prep
%setup -q

%build
make %{?_smp_mflags} DESTDIR=%{buildroot} PG_CONFIG=/usr/pgsql-12/bin/pg_config EXTRA_RUST_ARGS=--features=parse_headers

%install
make %{?_smp_mflags} DESTDIR=%{buildroot} PG_CONFIG=/usr/pgsql-12/bin/pg_config install

%files
%defattr(-,root,root,-)
%attr(0755,root,root) %dir %{_usr}/pgsql-12/lib
%attr(0755,root,root) %dir %{_usr}/pgsql-12/lib/bitcode
%attr(0755,root,root) %dir %{_usr}/pgsql-12/lib/bitcode/promscale
%attr(0755,root,root) %dir %{_usr}/pgsql-12/lib/bitcode/promscale/src
%attr(0755,root,root) %dir %{_usr}/pgsql-12/share/extension
%attr(0644,root,root) %{_usr}/pgsql-12/lib/bitcode/promscale.index.bc
%attr(0644,root,root) %{_usr}/pgsql-12/lib/bitcode/promscale/src/support.bc
%attr(0644,root,root) %{_usr}/pgsql-12/share/extension/promscale--0.1--0.1.1.sql
%attr(0644,root,root) %{_usr}/pgsql-12/share/extension/promscale--0.1.1.sql
%attr(0644,root,root) %{_usr}/pgsql-12/share/extension/promscale--0.1.sql
%attr(0755,root,root) %{_usr}/pgsql-12/lib/promscale.so
%attr(0755,root,root) %{_usr}/pgsql-12/share/extension/promscale.control

%changelog
* Tue Nov 3 2020 Matouš Jan Fialka <mjf@mjf.cz> - 0.1.1-1
- Initial packaging

# vi:ft=spec:tw=72:nowrap
