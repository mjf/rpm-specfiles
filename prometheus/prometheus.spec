# RPM specfile for Prometheus
# Copyright (C) 2020 Matous Jan Fialka, <mjf@mjf.cz>
# Released under the terms of the "MIT License"

Name            : prometheus
Version         : 2.22.1
Release         : 1%{?dist}
Group           : Network Servers
License         : ASL 2.0
Source          : https://github.com/prometheus/%{name}/releases/download/v%{version}/%{name}-%{version}.linux-amd64.tar.gz
URL             : https://prometheus.io
Summary         : Prometheus monitoring system and time series database
BuildRequires   : systemd-rpm-macros
Requires(pre)   : shadow-utils
Requires(postun): shadow-utils

%description
Prometheus is an open-source systems monitoring and alerting toolkit providing
a multi-dimensional data model with time series data identified by metric name
and key/value pairs, PromQL (a flexible query language to leverage this
dimensionality), collection of time series via a pull model (a push model via
Pushgateway), targets discovery via service discovery or static configuration
and of graphing and dashboarding support.

%define debug_package %{nil}

%undefine __brp_mangle_shebangs
%undefine __brp_ldconfig

%prep
%setup -q -n %{name}-%{version}.linux-amd64
%build

%install
install -d %{buildroot}%{_datadir}
install -d %{buildroot}%{_datadir}/%{name}
install -d %{buildroot}%{_localstatedir}/empty/%{name}
install -d %{buildroot}%{_sbindir}
install -d %{buildroot}%{_sharedstatedir}
install -d %{buildroot}%{_sharedstatedir}/%{name}
install -d %{buildroot}%{_sysconfdir}
install -d %{buildroot}%{_sysconfdir}/%{name}
install -d %{buildroot}%{_sysconfdir}/sysconfig
install -d %{buildroot}%{_unitdir}

install -t %{buildroot}%{_sbindir} %{name}
install -t %{buildroot}%{_sbindir} promtool
install -t %{buildroot}%{_sysconfdir}/%{name} %{name}.yml

for d in console_libraries consoles; do
  install -d %{buildroot}%{_datadir}/%{name}/$d
  for f in $d/*; do
    install -t %{buildroot}%{_datadir}/%{name}/$d $f
  done
done

cat > %{buildroot}%{_unitdir}/%{name}.service <<- EOT
[Unit]
Description=The Prometheus 2 monitoring system and time series database.
Documentation=https://prometheus.io
After=network.target

[Service]
Type=simple
User=%{name}
Group=%{name}
EnvironmentFile=-%{_sysconfdir}/sysconfig/%{name}
ExecStart=%{_sbindir}/%{name} --config.file=%{_sysconfdir}/%{name}/%{name}.yml --storage.tsdb.path=%{_sharedstatedir}/%{name} \$OPTIONS
ExecReload=/bin/kill -HUP \$MAINPID
Restart=on-failure
RestartSec=10
KillMode=mixed
KillSignal=SIGINT
ProtectSystem=full
NoNewPrivileges=true
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOT

cat > %{buildroot}%{_sysconfdir}/sysconfig/%{name} <<- EOT
OPTIONS="--web.console.libraries=%{_datadir}/%{name}/console_libraries --web.console.templates=%{_datadir}/%{name}/consoles"
EOT

%files
%defattr(-,root,root,-)
%attr(0755,root,root) %{_sbindir}/%{name}
%attr(0755,root,root) %{_sbindir}/promtool
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/%{name}.yml 
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%attr(0644,root,root) %{_unitdir}/%{name}.service
%attr(0755,%{name},%{name}) %dir %{_localstatedir}/empty/%{name}
%attr(0755,%{name},%{name}) %dir %{_sharedstatedir}/%{name}
%attr(0755,%{name},%{name}) %dir %{_datadir}/%{name}/console_libraries
%attr(0755,%{name},%{name}) %dir %{_datadir}/%{name}/consoles
%attr(0644,%{name},%{name}) %{_datadir}/%{name}/console_libraries/*
%attr(0644,%{name},%{name}) %{_datadir}/%{name}/consoles/*

%pre
getent passwd %{name} >/dev/null || useradd -Mrd %{_localstatedir}/empty/%{name} -s /sbin/nologin %{name}

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun %{name}.service
getent passwd %{name} >/dev/null && userdel %{name} 2>/dev/null

%changelog
* Tue Nov 3 2020 Matouš Jan Fialka <mjf@mjf.cz> 2.22.1-1
- Initial packaging

# vi:ft=spec:tw=72:nowrap
