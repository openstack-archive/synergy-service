#!/usr/bin/env bash
set -e -x

RPMBUILD=/home/pkger/rpmbuild
PKG_DIR=/tmp/synergy-service

function setup() {
    mkdir -p /home/pkger/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
    cd $RPMBUILD/SOURCES/
    cp -r $PKG_DIR python-synergy-service-$PKG_VERSION
    rm -r python-synergy-service-$PKG_VERSION/build || true
    tar cjf python-synergy-service-${PKG_VERSION}.tar.bz2 python-synergy-service-$PKG_VERSION
    cp $PKG_DIR/packaging/rpm/python-synergy.spec $RPMBUILD/SPECS/python-synergy.spec
}

function build() {
    cd $RPMBUILD/SPECS
    export PBR_VERSION=$PKG_VERSION
    rpmbuild -ba python-synergy.spec
    mkdir -p $PKG_DIR/build/
    cp -i $RPMBUILD/RPMS/noarch/python-synergy-service-*.rpm $PKG_DIR/build/
}

function clean() {
    rm -rf $RPMBUILD
}

clean
setup
build
