%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:             python-synergy-service
Version:          1.1.0
Release:          1%{?dist}
Summary:          Synergy service

License:          ASL 2.0
URL:              https://launchpad.net/synergy-service
Source0:          https://launchpad.net/synergy-service/%{name}-%{version}.tar.bz2

BuildArch:        noarch
BuildRequires:    systemd
BuildRequires:    python-devel
BuildRequires:    python-setuptools
Requires(pre):    shadow-utils
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
Requires:         python-eventlet >= 0.17
Requires:         python2-oslo-config >= 2.4
Requires:         python-pbr >= 1.8
Requires:         python-dateutil >= 2.4


%description
Synergy is as a new extensible general purpose management OpenStack service.
Its capabilities are implemented by a collection of managers which are
specific and independent pluggable tasks, executed periodically or
interactively. The managers can interact with each other in a loosely coupled
way.


%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

install -d -m0755                           %{buildroot}%{_sysconfdir}/synergy
install -D -m0644 config/synergy.conf       %{buildroot}%{_sysconfdir}/synergy/synergy.conf
install -D -m0644 scripts/synergy.service   %{buildroot}%{_unitdir}/synergy.service
install -d -m0700                           %{buildroot}%{_localstatedir}/lib/synergy
install -d -m0755                           %{buildroot}%{_localstatedir}/log/synergy
touch                                       %{buildroot}%{_localstatedir}/log/synergy/synergy.log
install -d -m0755                           %{buildroot}%{_localstatedir}/run/synergy
install -d -m0755                           %{buildroot}%{_localstatedir}/lock/synergy


%files
%doc README.rst
%{python_sitelib}/*
%config(noreplace) %{_sysconfdir}/synergy/synergy.conf
%{_bindir}/synergy
%{_bindir}/synergy-service
%{_unitdir}/synergy.service
%defattr(-, synergy, root, -)
%{_localstatedir}/lock/synergy/
%{_localstatedir}/log/synergy/
%{_localstatedir}/log/synergy/synergy.log
%{_localstatedir}/run/synergy/
%attr(700, synergy, root) %{_localstatedir}/lib/synergy/


%pre
getent group synergy > /dev/null || groupadd -r synergy
getent passwd synergy > /dev/null || \
    useradd -r -g synergy -s /sbin/nologin synergy
exit 0


%post
%systemd_post synergy.service


%preun
%systemd_preun synergy.service


%postun
%systemd_postun_with_restart synergy.service
if [ "$1" = 0 ]; then
    userdel -r synergy || true
    groupdel synergy || true
fi

%changelog
* Wed Sep 21 2016 Ervin Konomi <ervin.konomi@pd.infn.it - 1.1.0-1
- Improve Synergy serialization capabilities
- Streamline the packaging process
- Use dependency pinning for both CentOS and Ubuntu packaging

* Tue Jul 26 2016 Vincent Llorens <vincent.llorens@cc.in2p3.fr - 1.0.1-1
- Fix broken links in README

* Fri Jun 17 2016 Vincent Llorens <vincent.llorens@cc.in2p3.fr> - 1.0.0-1
- First public release of Synergy. Full set of functionalities.

* Fri Apr 29 2016 Vincent Llorens <vincent.llorens@cc.in2p3.fr> - 0.2-2
- Working release with minimum set of functionalities

* Wed Jan 20 2016 Vincent Llorens <vincent.llorens@cc.in2p3.fr>
- WIP RPM release
