%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:             python-synergy-service
Version:          1.5.3
Release:          2%{?dist}
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
Requires:         python2-eventlet
Requires:         python2-oslo-config
Requires:         python2-pbr
Requires:         python-dateutil
Requires:         python2-requests


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
%{_localstatedir}/run/synergy/
%attr(700, synergy, root) %{_localstatedir}/lib/synergy/


%pre
getent group synergy > /dev/null || groupadd -r synergy
getent passwd synergy > /dev/null || \
    useradd -r -g synergy -s /sbin/nologin synergy
exit 0


%preun
%systemd_preun synergy.service


%postun
if [ "$1" = 0 ]; then
    userdel -r synergy 2> /dev/null || true
    groupdel synergy 2> /dev/null || true
fi

%changelog
* Wed Sep 20 2017 Ervin Konomi <ervin.konomi@pd.infn.it> - 1.5.3-1
- Shell version updated
- Authorization section updated
- Update RPM package dependencies

* Mon Aug 21 2017 Vincent Llorens <vincent.llorens@cc.in2p3.fr> - 1.5.2-2
- Update some python requirements to python2-* names

* Tue Jul 18 2017 Ervin Konomi <ervin.konomi@pd.infn.it> - 1.5.2-1
- Fixes on the authorization mechanism
- Enhancement in handling the parameters defined in the user request
- Missing security support
- Synergy should never raise Exception directly
- manager.notify() doesn't handle the NotImplementedError exceptions
- The synergy.log doesn't contain all logged messages

* Tue Mar 21 2017 Ervin Konomi <ervin.konomi@pd.infn.it> - 1.5.1-1
- Update synergy service packaging

* Mon Mar 20 2017 Ervin Konomi <ervin.konomi@pd.infn.it> - 1.5.0-1
- add some unit tests for Trust
- CLI: remove auth_token, unused vars and add tests
- add some unit tests for ExecuteCommand
- add some unit tests for the ManagerCommand class
- simplify packaging with docker
- fix one instance of "except Exception"
- add some unit tests for HTTPCommand
- fix missing elements in string formatting
- remove support for SysV init and Upstart
- Removed all managers parameters in synergy.conf
- fix synergy erasing log file on upgrade

* Mon Jan 30 2017 Ervin Konomi <ervin.konomi@pd.infn.it> - 1.4.0-1
- Update of the links to the Synergy documentation
- Update of the Synergy configuration file
- The Synergy CLI is not SSL-enabled

* Tue Dec 06 2016 Vincent Llorens <vincent.llorens@cc.in2p3.fr> - 1.3.0-1
- Replaces uuid.uuid4 with uuidutils.generate_uuid
- [packaging] make docker aware of PKG_VERSION
- Added support for OpenStack DOMAIN to shell.py
- Update changelogs and system package versions
- Clean up oslo imports
- Update the Sphinx documentation
- fix packaging with docker and its documentation
- Distribute tabulate as part of Synergy
- Remove versions for required packages
- fix missing "requests" from the requirements
- Updated coverage configuration file
- fix docker packaging for CentOS
- fix wrong version of eventlet
- fix docs for packaging with Ubuntu
- fix to get the synergy version when packaging
- fix required packages when packaging

* Wed Nov 09 2016 Vincent Llorens <vincent.llorens@cc.in2p3.fr> - 1.2.0-1
- use pbr fully for easier package building
- RPM: don't output errors on uninstallation
- Fix conf for AMQP virtual host
- Added unit tests
- Fixed destroy() method
- Fixed serializer
- Fixed logging for managers
- fix eventlet and dateutil required versions
- Fix requirement version pinning

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
