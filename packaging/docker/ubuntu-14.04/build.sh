#!/usr/bin/env bash
set -e -x

PKG_DIR=/tmp/synergy

function copy_source() {
    cd /home/pkger
    cp -r $PKG_DIR python-synergy-service
    rm -r python-synergy-service/{.eggs,.tox,.testrepository,build,dist} || true
}

function get_version() {
    if [[ -z $PKG_VERSION ]]; then
        cd $PKG_DIR
        export PKG_VERSION=$(git tag -l "*.*.*" | sort -V | tail -1)
    fi
}

function setup() {
    cd /home/pkger
    tar cjf python-synergy-service_${PKG_VERSION}.orig.tar.bz2 python-synergy-service
    mv python-synergy-service/packaging/debian python-synergy-service/debian
}

function build() {
    cd /home/pkger/python-synergy-service
    debuild -us -uc
    mkdir -p $PKG_DIR/build
    cp -i /home/pkger/*.deb $PKG_DIR/build
}

function clean() {
    rm -r /home/pkger/python-synergy-service{,_${PKG_VERSION}.orig.tar.bz2}
}

clean || true
copy_source
get_version
setup
build
