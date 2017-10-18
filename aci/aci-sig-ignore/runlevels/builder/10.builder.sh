#!/bin/bash

set -e
. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x

export GOROOT=/usr/local/go
export GOPATH=/go

mkdir -pv ${GOPATH}

cd ${ACI_HOME}/src/

go build .
mv -v src ${ROOTFS}/sig