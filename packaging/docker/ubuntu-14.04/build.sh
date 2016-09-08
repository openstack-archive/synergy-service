#!/usr/bin/env bash
set -e -x

PKG_DIR=/tmp/synergy-service

function copy_source() {
    cd /home/pkger
    cp -r $PKG_DIR python-synergy-service
    rm -r python-synergy-service/{.tox,.testrepository,build,dist} || true
}

function get_version() {
    local file=/home/pkger/python-synergy-service/setup.cfg
    export PKG_VERSION=$(grep -e "version = " $file | sed -r "s/version = ()/\1/")
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
