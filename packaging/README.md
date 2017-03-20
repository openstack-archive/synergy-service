Packaging
=========

Packaging for Ubuntu and CentOS using Docker
--------------------------------------------

We provide Dockerfiles for CentOS 7 and Ubuntu 16.04.  A Dockerfile for Ubuntu >
16.04 should work by just changing the "FROM" statement of the Ubuntu 16.04
Dockerfile.  Using these, you can easily build rpm and deb packages for
synergy-service without having to setup the build system on your own system.

The build process using Docker is made of 3 steps:

1. Build the docker image

2. Setup the build variables

3. Run the build with docker

If the build is successful, the package will be put in the build directory
inside the synergy-service directory.


### Example for CentOS 7

- go into the directory that contains the Dockerfile for CentOS 7

      cd synergy-service/packaging/docker/centos7

- build the docker image and tag it

      docker build -t synergy-centos7-builder .

- launch the container

      docker run -i -v /path/to/synergy-service:/tmp/synergy \
                 synergy-centos7-builder

  You can override the package version that will be set during the packaging
  process by adding `-e "PKG_VERSION=x.y.z"` to the above command line.
  Otherwise, the package version will be set to the latest git tag.

  This actually mount the synergy-service directory to `/tmp/synergy` on
  the guest.

- the resulting rpm should be in the build directory if successful


### Example for Ubuntu 16.04

- go into the directory that contains the Dockerfile for Ubuntu 16.04

      cd synergy-service/packaging/docker/ubuntu-16.04

- build the docker image and tag it

      docker build -t synergy-ubuntu16.04-builder .


- launch the container

      docker run -i -v /path/to/synergy-service:/tmp/synergy \
                 synergy-ubuntu16.04-builder

  You can override the package version that will be set during the packaging
  process by adding `-e "PKG_VERSION=x.y.z"` to the above command line.
  Otherwise, the package version will be set to the latest git tag.

- the resulting deb should be in the build directory if successful


Packaging for Ubuntu
--------------------

Make sure you have the [OpenStack/CloudArchive repository](https://wiki.ubuntu.com/OpenStack/CloudArchive) setup.

1. Install the necessary build packages:
  - debhelper
  - dh-systemd
  - build-essential
  - devscripts
  - git-core
  - python-all
  - python-pbr
  - python-setuptools

2. Make a gzip archive of synergy-service named `python-synergy-service_VERSION.orig.tar.gz` and place it at the same level as the `synergy-service` directory.

3. Copy `synergy-service/packaging/debian` to `synergy-service/debian`.

4. Go in the `synergy-service` directory and build with `debuild -us -uc`.

The resulting .deb file should be outputed at the same level as the `synergy-service` directory and .tar.gz archive.


Packaging for CentOS
--------------------

1. Install the necessary build packages:
  - rpm-build
  - python-devel
  - python-setuptools
  - git-core
  - centos-release-openstack-newton

2. Update your packages with `yum update` and then install `python-pbr`.

3. Setup your rpmbuild environment if not already done.

       mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

4. Move `synergy-service/packaging/rpm/python-synergy.spec` to
   `~/rpmbuild/SPECS`.

5. Create a source archive (where $VERSION is the current synergy-service version):

       cd ~/rpmbuild/SOURCES
       cp -r /path/to/synergy-service python-synergy-service-$VERSION
       tar cjf python-synergy-service-$VERSION.tar.bz2 python-synergy-service-$VERSION

6. Go in `~/rpmbuild/SPECS` and build with `PBR_VERSION=$VERSION rpmbuild -ba python-synergy.spec`.

7. The resulting RPM can be found in `~/rpmbuild/RPMS/noarch`.
