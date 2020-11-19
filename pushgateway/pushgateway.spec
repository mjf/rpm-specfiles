# RPM specfile for Prometheus Pushgateway
# Copyright (C) 2020 Matous Jan Fialka, <mjf@mjf.cz>
# Released under the terms of the "MIT License"

Name            : pushgateway
Version         : 1.3.0
Release         : 1%{?dist}
Group           : Network Servers
License         : Apache License 2.0
Source          : https://github.com/prometheus/%{name}/releases/download/v%{version}/%{name}-%{version}.linux-amd64.tar.gz
URL             : https://github.com/prometheus/%{name}
Summary         : Prometheus Pushgateway for ephemeral and batch jobs
BuildRequires   : systemd-rpm-macros
Requires(pre)   : shadow-utils
Requires(postun): shadow-utils

%description
Prometheus Pushgateway for ephemeral and batch jobs allowing to expose their
metrics to Prometheus.

%define debug_package %{nil}

%undefine __brp_mangle_shebangs
%undefine __brp_ldconfig

%prep
%setup -q -n %{name}-%{version}.linux-amd64
%build

%install
install -d %{buildroot}%{_localstatedir}
install -d %{buildroot}%{_localstatedir}/empty
install -d %{buildroot}%{_localstatedir}/empty/%{name}
install -d %{buildroot}%{_sbindir}
install -d %{buildroot}%{_sysconfdir}
install -d %{buildroot}%{_sysconfdir}/sysconfig
install -d %{buildroot}%{_unitdir}

install -t %{buildroot}%{_sbindir} %{name}

cat > %{buildroot}%{_unitdir}/%{name}.service <<- EOT
[Unit]
Description=Prometheus Pushgateway for ephemeral and batch jobs
Documentation=https://github.com/prometheus/%{name}
After=syslog.target
After=network.target

[Service]
Type=simple
User=%{name}
Group=%{name}
EnvironmentFile=-/etc/sysconfig/%{name}
ExecStart=/usr/sbin/%{name} \$OPTIONS
Restart=on-failure
RestartSec=10
KillMode=mixed
KillSignal=SIGINT
ProtectSystem=strict
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOT

cat > %{buildroot}%{_sysconfdir}/sysconfig/%{name} <<- EOT
# OPTIONS=""
EOT

%files
%defattr(-,root,root,-)
%attr(0755,root,root) %{_sbindir}/%{name}
%attr(0644,root,root) %{_unitdir}/%{name}.service
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%attr(0755,%{name},%{name}) %dir %{_localstatedir}/empty/%{name}

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
* Tue Nov 3 2020 Matouš Jan Fialka <mjf@mjf.cz> -1.3.0-1
- Initial packaging

# vi:ft=spec:tw=72:nowrap
