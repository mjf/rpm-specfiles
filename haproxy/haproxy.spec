# RPM specfile for the HAProxy Load Balancer
# Copyright (C) 2017-2019 Matouš Jan Fialka, <https://mjf.cz/>
# Released under the terms of "The MIT License"

# Usage: rpmbuild -ba haproxy.spec \
#        [--undefine=_disable_source_fetch]

# global
%global _hardened_build    1
%global _performance_build 1

# package release
%define package_name    haproxy
%define package_release 1
%define package_vendor  mjf

# haproxy
%define haproxy_version     2.3
%define haproxy_release     2
%define haproxy_user        haproxy
%define haproxy_uid         188
%define haproxy_group       %{haproxy_user}
%define haproxy_gid         %{haproxy_uid}
%define haproxy_homedir     %{_localstatedir}/lib/haproxy
%define haproxy_confdir     %{_sysconfdir}/haproxy
%define haproxy_tmpfilesdir %{_sysconfdir}/tmpfiles.d
%define haproxy_libdir      %{_sharedstatedir}/haproxy
%define haproxy_chrootdir   %{_var}/empty/haproxy
%define haproxy_rundir      /run/haproxy

# library
%define openssl_version 1.1.1i

# package information
Name:      %{package_name}
Version:   %{haproxy_version}.%{haproxy_release}
Release:   %{package_release}.%{package_vendor}%{?dist}
Summary:   HAProxy Load Balancer
URL:       https://www.haproxy.org
License:   GPLv2+
Group:     HAProxy
Provides:  %{package_name}%{?_isa} = %{version}-%{release}
Conflicts: %{package_name}%{?_isa} < %{version}-%{release}

# requirements
Requires:         epel-release
Requires:         ius-release
Requires:         lua53u
Requires(pre):    shadow-utils
Requires(preun):  systemd
Requires(post):   systemd
Requires(postun): systemd

# build requirements
BuildRequires: gcc
BuildRequires: systemd-devel
BuildRequires: pcre-devel
BuildRequires: zlib-devel
BuildRequires: lua53u-devel
BuildRequires: python-sphinx

# sources
Source0: https://www.haproxy.org/download/%{haproxy_version}/src/haproxy-%{version}.tar.gz
Source1: https://www.openssl.org/source/openssl-%{openssl_version}.tar.gz

# description
%description
HAProxy Load Balancer with recent OpenSSL and Prometheus metrics service

# miscellanea
%define __perl_requires %{nil}

%prep

%setup -q -n %{package_name}-%{version}

%build
mkdir -p %{_tmppath}/local

# make openssl
tar -xzvf %{SOURCE1} -C %{_tmppath}/local
pushd %{_tmppath}/local/openssl-%{openssl_version}
./Configure --prefix=%{_tmppath}/local \
  -DSSL_ALLOW_ADH \
  no-shared \
  no-tls1 \
  no-weak-ssl-ciphers \
  no-zlib \
%ifarch %ix86 x86_64
  linux-x86_64
%endif
old_rpm_opt_flags="$RPM_OPT_FLAGS"
RPM_OPT_FLAGS="$RPM_OPT_FLAGS -Wa,--noexecstack -DPURIFY"
%{__make} -j$(nproc) %{?_smp_mflags}
%{__make} -j$(nproc) install_sw
RPM_OPT_FLAGS="$old_rpm_opt_flags"
popd

# make haproxy
%{__make} -j$(nproc) %{?_smp_mflags} ARCH=%{_target_cpu} TARGET=linux-glibc \
%ifarch %ix86 x86_64
  USE_REGPARM=1 \
%endif
  USE_LINUX_TPROXY=1 \
  USE_TFO=1 \
  USE_NS=1 \
  USE_SYSTEMD=1 \
  USE_OPENSSL=1 \
  USE_ZLIB=1 \
  USE_PCRE=1 \
  USE_PCRE_JIT=1 \
  USE_LUA=1 \
  SSL_LIB=%{_tmppath}/local/lib \
  SSL_INC=%{_tmppath}/local/include \
  LUA_LIB_NAME=lua-5.3 \
  LUA_LIB=%{_libdir}/lua/5.3 \
  LUA_INC=%{_includedir}/lua-5.3 \
  ADDINC='%{optflags}' \
  ADDLIB='%{__global_ldflags} -pthread' \
  DEFINE='-DTCP_USER_TIMEOUT=18 -DMAX_SESS_STKCTR=12' \
  EXTRA_OBJS='contrib/prometheus-exporter/service-prometheus.o'

# make halog
%{__make} -C contrib/halog

# make haproxy tools
%{__make} -C contrib/ip6range
%{__make} -C contrib/iprange
%{__make} -C contrib/tcploop

# make manuals
pushd doc/lua-api
%{__make} man
gzip -9 _build/man/haproxy-lua.1
popd

# make systemd service
cat >haproxy.service <<- EOT
[Unit]
Description=HAProxy Load Balancer
Documentation=whatis:haproxy man:haproxy(1) http://cbonte.github.io/haproxy-dconv/%{haproxy_version}/intro.html
After=network-online.target
Wants=network-online.target

[Service]
UMask=077
AssertPathExists=%{_sysconfdir}/sysconfig/haproxy
EnvironmentFile=-%{_sysconfdir}/sysconfig/haproxy
ExecStartPre=%{_sbindir}/haproxy -f "\$CONFIGDIR" -C "\$CONFIGDIR" -c -q -L "\$LOCAL_PEER_NAME"
#ExecStartPre=-%{_bindir}/mkdir "%{haproxy_chrootdir}/dev"
#ExecStartPre=-%{_bindir}/mknod "%{haproxy_chrootdir}/dev/random" c 1 8
#ExecStartPre=-%{_bindir}/mknod "%{haproxy_chrootdir}/dev/urandom" c 1 9
ExecStart=%{_sbindir}/haproxy -Ws -f "\$CONFIGDIR" -C "\$CONFIGDIR" -p "\$MASTER_PIDFILE" -sf "\$(cat \$MASTER_PIDFILE)" -L "\$LOCAL_PEER_NAME" \$EXTRA_START_OPTS
ExecReload=%{_sbindir}/haproxy -f "\$CONFIGDIR" -C "\$CONFIGDIR" -c -q -L "\$LOCAL_PEER_NAME" \$EXTRA_RELOAD_OPTS
ExecReload=%{_bindir}/kill -USR2 \$MAINPID
ExecStopPost=%{_bindir}/rm "\$MASTER_SOCKET" "\$MASTER_PIDFILE" "\$STATS_SOCKET"
Type=notify
NotifyAccess=main
KillMode=mixed
KillSignal=USR1
Restart=always
SuccessExitStatus=143
OOMScoreAdjust=-999
NoNewPrivileges=true
ProtectHome=true
ProtectSystem=true
SystemCallFilter=~@cpu-emulation @keyring @module @obsolete @raw-io @reboot @swap @sync

[Install]
WantedBy=multi-user.target
EOT

# make sysconfig
cat >haproxy.sysconfig <<- EOT
CONFIGDIR='%{_sysconfdir}/haproxy'
MASTER_PIDFILE='%{haproxy_rundir}/master.pid'
MASTER_SOCKET='%{haproxy_rundir}/master.sock'
STATS_SOCKET='%{haproxy_rundir}/stats.sock'
LOCAL_PEER_NAME="\$HOSTNAME"
EXTRA_START_OPTS="-S \$MASTER_SOCKET"
EXTRA_RELOAD_OPTS=""
EOT

# make haproxy config
cat >haproxy.cfg <<- EOT
global

    user haproxy
    group haproxy

    chroot %{haproxy_chrootdir}

    stats socket \$STATS_SOCKET mode 0600 expose-fd listeners level user
    stats timeout 2m

defaults

    mode tcp

    timeout client 5s
    timeout connect 5s
    timeout server 5s

frontend stats

    bind *:8404

    mode http

    option http-use-htx

    http-request use-service prometheus-exporter if { path /metrics }

    stats enable
    stats uri /stats
    stats refresh 10s
EOT

cat >haproxy.tmpfiles <<- EOT
d %{haproxy_rundir} 0700 %{haproxy_user} %{haproxy_group} -
EOT

%clean
[ %{buildroot} = / ] || rm -r -f %{buildroot}
[ %{_tmppath}/local = / ] || rm -r -f %{_tmppath}/local

%pre
getent group %{haproxy_group} &>/dev/null || \
  groupadd %{haproxy_group} \
    -r \
    -g %{haproxy_gid}

getent passwd %{haproxy_user} &>/dev/null || \
  useradd %{haproxy_user} \
    -r \
    -u %{haproxy_uid} \
    -g %{haproxy_group} \
    -d %{haproxy_homedir} \
    -c 'HAProxy Load Balancer' \
    -s /sbin/nologin

exit 0

%install
umask 077

%{__make} install-bin DESTDIR=%{buildroot} PREFIX=%{_prefix}
%{__make} install-man DESTDIR=%{buildroot} PREFIX=%{_prefix}

install -d %{buildroot}%{haproxy_chrootdir}
install -d %{buildroot}%{haproxy_confdir}
install -d %{buildroot}%{haproxy_homedir}
install -d %{buildroot}%{haproxy_libdir}
install -d %{buildroot}%{haproxy_rundir}

# haproxy package
install -D doc/lua-api/_build/man/haproxy-lua.1.gz %{buildroot}%{_mandir}/man1/haproxy-lua.1.gz

install -D haproxy.cfg       %{buildroot}%{haproxy_confdir}/haproxy.cfg
install -D haproxy.tmpfiles  %{buildroot}%{haproxy_tmpfilesdir}/haproxy.conf
install -D haproxy.service   %{buildroot}%{_unitdir}/haproxy.service
install -D haproxy.sysconfig %{buildroot}%{_sysconfdir}/sysconfig/haproxy

# haproxy-halog package
install -D contrib/halog/halog %{buildroot}%{_sbindir}/halog

# haproxy-tools package
install -D contrib/ip6range/ip6range %{buildroot}%{_bindir}/ip6range
install -D contrib/iprange/iprange   %{buildroot}%{_bindir}/iprange
install -D contrib/tcploop/tcploop   %{buildroot}%{_bindir}/tcploop

%post
%systemd_post haproxy.service

%preun
%systemd_preun haproxy.service

%postun
%systemd_postun_with_restart haproxy.service

%files
%defattr(-,root,root,-)

%attr(0700,root,root) %dir %{haproxy_confdir}
%attr(0700,root,root) %dir %{haproxy_homedir}
%attr(0700,root,root) %dir %{haproxy_libdir}

%attr(0700,%{haproxy_user},%{haproxy_group}) %dir %{haproxy_chrootdir}
%attr(0700,%{haproxy_user},%{haproxy_group}) %dir %{haproxy_rundir}

%attr(0755,root,root) %{_sbindir}/haproxy
%attr(0644,root,root) %{_unitdir}/haproxy.service

%attr(0644,root,root) %config(noreplace) %{haproxy_confdir}/haproxy.cfg
%attr(0644,root,root) %config(noreplace) %{haproxy_tmpfilesdir}/haproxy.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/sysconfig/haproxy

%attr(0644,root,root) %doc CHANGELOG
%attr(0644,root,root) %doc CONTRIBUTING
%attr(0644,root,root) %doc INSTALL
%attr(0644,root,root) %doc LICENSE
%attr(0644,root,root) %doc MAINTAINERS
%attr(0644,root,root) %doc README
%attr(0644,root,root) %doc ROADMAP
%attr(0644,root,root) %doc SUBVERS
%attr(0644,root,root) %doc VERDATE
%attr(0644,root,root) %doc VERSION

%attr(0644,root,root) %doc doc/architecture.txt
%attr(0644,root,root) %doc doc/configuration.txt
%attr(0644,root,root) %doc doc/gpl.txt
%attr(0644,root,root) %doc doc/internals/acl.txt
%attr(0644,root,root) %doc doc/intro.txt
%attr(0644,root,root) %doc doc/lgpl.txt
%attr(0644,root,root) %doc doc/management.txt
%attr(0644,root,root) %doc doc/network-namespaces.txt
%attr(0644,root,root) %doc doc/proxy-protocol.txt
%attr(0644,root,root) %doc doc/proxy-protocol.txt
%attr(0644,root,root) %doc doc/SPOE.txt

%attr(0644,root,root) %doc %{_mandir}/man1/haproxy.1.gz
%attr(0644,root,root) %doc %{_mandir}/man1/haproxy-lua.1.gz

%attr(0644,root,root) %license LICENSE
%attr(0644,root,root) %license doc/gpl.txt
%attr(0644,root,root) %license doc/lgpl.txt

# haproxy-halog package
%package halog
Summary: HAProxy Log Statistics Reporter
Group: HAProxy

%description halog
HAProxy tool for log statistics reporting

%files halog
%defattr(-,root,root,-)
%attr(0755,root,root) %{_sbindir}/halog

# haproxy-tools package
%package tools
Summary: HAProxy Tools
Group: HAProxy

%description tools
HAProxy tools for HPACK decoding, TCP testing, debugging and more

%files tools
%defattr(-,root,root,-)
%attr(0755,root,root) %{_bindir}/ip6range
%attr(0755,root,root) %{_bindir}/iprange
%attr(0755,root,root) %{_bindir}/tcploop

%changelog
* Thu Nov 19 2020 Matouš Jan Fialka <mjf@mjf.cz> - 2.3.1-1.mjf.el7.centos
- Initial packaging of HAProxy v2.3.1 with OpenSSL v1.1.1h

# vi:nowrap:
