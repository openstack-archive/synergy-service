#!/usr/bin/env bash
set -e -x

PKG_DIR=/tmp/synergy-service

function setup() {
    cd /home/pkger
    cp -r $PKG_DIR synergy-service
    tar cfz python-synergy-service_${PKG_VERSION}.orig.tar.gz synergy-service
    mv synergy-service python-synergy-service
    cp -r python-synergy-service/packaging/debian python-synergy-service/debian
}

function build() {
    cd /home/pkger/python-synergy-service
    debuild -us -uc
    mkdir -p $PKG_DIR/build
    cp -i /home/pkger/*.deb $PKG_DIR/build
}

function clean() {
    rm -r /home/pkger/python-synergy-service*
}

setup
build
clean
