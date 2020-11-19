# RPM specfile for the InfluxDB OSS 2 Time Series Platform
# Copyright (C) 2020 Matouš Jan Fialka, <https://mjf.cz/>
# Released under the terms of "The MIT License"

# Usage: rpmbuild -ba influxdb2.spec \
         [--undefine=_disable_source_fetch]

# global
%global _hardened_build    1
%global _performance_build 1

# package release
%define package_name    influxdb2
%define package_release 1
%define package_vendor  mjf

# influxdb2
%define influxdb2_version     2.0.0
%define influxdb2_release     beta.16
%define influxdb2_user        influxdb2
%define influxdb2_uid         199
%define influxdb2_group       %{influxdb2_user}
%define influxdb2_gid         %{influxdb2_uid}
%define influxdb2_homedir     %{_localstatedir}/lib/influxdb2
%define influxdb2_rundir      /run

# package information
Name:      %{package_name}
Version:   %{influxdb2_version}.%{influxdb2_release}
Release:   %{package_release}.%{package_vendor}%{?dist}
Summary:   InfluxDB OSS 2 Time Series Platform
URL:       https://www.influxdata.com/products/influxdb-overview/
License:   MIT
Group:     Network Servers
Provides:  %{package_name}%{?_isa} = %{version}-%{release}
Conflicts: %{package_name}%{?_isa} < %{version}-%{release}

# requirements
Requires(pre):    shadow-utils
Requires(preun):  systemd
Requires(post):   systemd
Requires(postun): systemd

# sources
Source0: https://dl.influxdata.com/influxdb/releases/influxdb_%{influxdb2_version}-%{influxdb2_release}_linux_amd64.tar.gz

# description
%description
The InfluxDB 2 time series platform is purpose-built to collect, store, process
and visualize metrics and events. InfluxDB OSS 2 is the open source version of
InfluxDB 2.

# miscellanea
%define __perl_requires %{nil}

%prep

%setup -q -n influxdb_%{influxdb2_version}-%{influxdb2_release}_linux_amd64

%build
# make influx{,d}2 files
mv influx{,2}
mv influxd{,2}

# make systemd service
cat >influxd2.service <<- EOT
[Unit]
Description=InfluxDB OSS 2 Time Series Platform
Documentation=https://v2.docs.influxdata.com/v2.0/
After=network.target
AssertPathExists=%{_sysconfdir}/sysconfig/influxd2
AssertPathExists=%{influxdb2_homedir}
AssertPathExists=%{influxdb2_homedir}/engine

[Service]
UMask=077
EnvironmentFile=-%{_sysconfdir}/sysconfig/influxd2
ExecStart=%{_sbindir}/influxd2 \$INFLUXD2_OPTS
User=%{influxdb2_user}
Group=%{influxdb2_group}
Restart=on-failure
OOMScoreAdjust=-999
NoNewPrivileges=true
ProtectHome=true
ProtectSystem=true

[Install]
WantedBy=multi-user.target
EOT

# make sysconfig
cat >influxd2.sysconfig <<- EOT
INFLUXD2_OPTS="--reporting-disabled --bolt-path %{influxdb2_homedir}/influxd.bolt --engine-path %{influxdb2_homedir}/engine --http-bind-address=0.0.0.0:9999"
EOT

%clean
[ %{buildroot} = / ] || rm -r -f %{buildroot}

%pre
getent group %{influxdb2_group} &>/dev/null || \
  groupadd %{influxdb2_group} \
    -r \
    -g %{influxdb2_gid}

getent passwd %{influxdb2_user} &>/dev/null || \
  useradd %{influxdb2_user} \
    -r \
    -u %{influxdb2_uid} \
    -g %{influxdb2_group} \
    -d %{influxdb2_homedir} \
    -c 'InfluxDB OSS 2 Time Series Platform' \
    -s /sbin/nologin

exit 0

%install
umask 077

install -d %{buildroot}%{influxdb2_homedir}
install -d %{buildroot}%{influxdb2_homedir}/engine

install -D influx2            %{buildroot}%{_bindir}/influx2
install -D influxd2           %{buildroot}%{_sbindir}/influxd2
install -D influxd2.service   %{buildroot}%{_unitdir}/influxd2.service
install -D influxd2.sysconfig %{buildroot}%{_sysconfdir}/sysconfig/influxd2

%post
%systemd_post influxd2.service

%preun
%systemd_preun influxd2.service

%postun
%systemd_postun_with_restart influxd2.service

%files
%defattr(-,root,root,-)

%attr(0700,%{influxdb2_user},%{influxdb2_group}) %dir %{influxdb2_homedir}
%attr(0700,%{influxdb2_user},%{influxdb2_group}) %dir %{influxdb2_homedir}/engine

%attr(0755,root,root) %{_bindir}/influx2
%attr(0755,root,root) %{_sbindir}/influxd2
%attr(0644,root,root) %{_unitdir}/influxd2.service

%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/sysconfig/influxd2

%changelog
* Fri Jul 31 2020 Matouš Jan Fialka <mjf@mjf.cz> - 2.0.0.beta.15-1.mjf.el8.centos
- Update to version 2.0.0.beta.15

* Wed Jul 8 2020 Matouš Jan Fialka <mjf@mjf.cz> - 2.0.0.beta.13-1.mjf.el8.centos
- Update to version 2.0.0.beta.13

* Wed Jun 16 2020 Matouš Jan Fialka <mjf@mjf.cz> - 2.0.0.beta.12-1.mjf.el8.centos
- Update to version 2.0.0.beta.12

* Wed Jun 10 2020 Matouš Jan Fialka <mjf@mjf.cz> - 2.0.0.beta.10-1.mjf.el8.centos
- Initial packaging

# vi:nowrap:
