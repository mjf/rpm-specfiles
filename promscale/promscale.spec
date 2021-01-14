# RPM specfile for Promscale
# Copyright (C) 2020 Matous Jan Fialka, <mjf@mjf.cz>
# Released under the terms of the "MIT License"

Name            : promscale
Version         : 0.1.4
Release         : 1%{?dist}
Group           : Network Servers
License         : Apache License 2.0
Source          : https://github.com/timescale/%{name}/archive/%{version}.tar.gz#/%{name}-%{version}.tgz
URL             : https://github.com/timescale/%{name}
Summary         : An analytical platform and long-term store for Prometheus
BuildRequires   : golang
BuildRequires   : systemd-rpm-macros
Requires(pre)   : shadow-utils
Requires(postun): shadow-utils


%description
Promscale is a horizontally scalable and operationally mature analytical
platform for Prometheus data that offers the combined power of PromQL
and SQL, enabling developers to ask any question, create any dashboard,
and achieve greater visibility into their systems.  Promscale is built
on top of TimescaleDB, the relational database for time-series built on
top of PostgreSQL.

%define debug_package %{nil}

%undefine __brp_mangle_shebangs
%undefine __brp_ldconfig

%prep
%setup -q

%build
go mod vendor

cd cmd/%{name}
go build -mod=vendor -buildmode=pie -trimpath

%install
install -d %{buildroot}%{_localstatedir}
install -d %{buildroot}%{_localstatedir}/empty
install -d %{buildroot}%{_localstatedir}/empty/%{name}
install -d %{buildroot}%{_sbindir}
install -d %{buildroot}%{_sysconfdir}
install -d %{buildroot}%{_sysconfdir}/sysconfig
install -d %{buildroot}%{_unitdir}

install -t %{buildroot}%{_sbindir} cmd/%{name}/%{name}
cat > %{buildroot}%{_unitdir}/%{name}.service <<- EOT
[Unit]
Description=TimescaleDB Promscale Service
Documentation=https://github.com/timescale/%{name}
After=syslog.target
After=network.target

[Service]
Type=simple
User=%{name}
Group=%{name}
EnvironmentFile=-%{_sysconfdir}/sysconfig/%{name}
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
# TS_PROM_ASYNC_ACKS=""
# TS_PROM_DB_CONNECT_RETRIES=""
# TS_PROM_DB_CONNECTIONS_MAX="-1"
# TS_PROM_DB_HOST="localhost"
# TS_PROM_DB_NAME="timescale"
# TS_PROM_DB_PASSWORD=""
# TS_PROM_DB_PORT="5432"
TS_PROM_DB_SSL_MODE="disable"
# TS_PROM_DB_USER="postgres"
# TS_PROM_DB_WRITER_CONNECTION_CONCURRENCY="4"
# TS_PROM_INSTALL_TIMESCALEDB="true"
# TS_PROM_LABELS_CACHE_SIZE="10000"
# TS_PROM_LEADER_ELECTION_PG_ADVISORY_LOCK_ID=""
# TS_PROM_LEADER_ELECTION_PG_ADVISORY_LOCK_PROMETHEUS_TIMEOUT="-1ns"
# TS_PROM_LEADER_ELECTION_REST=""
# TS_PROM_LOG_FORMAT="logfmt"
# TS_PROM_METRICS_CACHE_SIZE="10000"
# TS_PROM_MIGRATE="true"
# TS_PROM_SCHEDULED_ELECTION_INTERVAL="5s"
# TS_PROM_TPUT_REPORT=""
# TS_PROM_USE_SCHEMA_VERSION_LEASE=""
# TS_PROM_WEB_CORS_ORIGIN=".*"
# TS_PROM_WEB_LISTEN_ADDRESS=":9201"
# TS_PROM_WEB_TELEMETRY_PATH="/metrics"

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
* Thu Nov 12 2020 Matouš Jan Fialka <mjf@mjf.cz> - 0.1.2-1
- Raise version to v0.1.12 release

* Tue Nov 3 2020 Matouš Jan Fialka <mjf@mjf.cz> - 0.1.1-1
- Initial packaging

# vi:ft=spec:tw=72:nowrap
