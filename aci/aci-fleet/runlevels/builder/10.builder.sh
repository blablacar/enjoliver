#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -e

set -o pipefail

export LC_ALL=C
export GOROOT=/usr/local/go
export GOPATH=/go
export PATH=$PATH:/go/bin:/usr/local/go/bin


# Fetch sources
WORK_DIR="${GOPATH}/src/github.com/coreos/fleet"
go get -d github.com/coreos/fleet
cd ${WORK_DIR}
git checkout v${ACI_VERSION}
# Apply custom patches
PATCHES_DIR="${ACI_HOME}/patches"
for patch in $(ls $PATCHES_DIR)
do
    echo "${PATCHES_DIR}/${patch}"
    head -4 "${PATCHES_DIR}/${patch}"
    patch -p1 < "${PATCHES_DIR}/${patch}" || {
        echo >&2 "Unable to apply patch ${patch}"
        exit 1
    }
    echo ""
done
export VERSION=$(git describe --dirty)
# Build
export GLDFLAGS="-X github.com/coreos/fleet/version.Version=${VERSION} -s -v -extldflags '-static'"
CGO_ENABLED=0 go build -o bin/fleetd -a -installsuffix netgo -ldflags "${GLDFLAGS}"
CGO_ENABLED=0 go build -o bin/fleetctl -a -installsuffix netgo -ldflags "${GLDFLAGS}" ./fleetctl
upx -q bin/fleetctl
upx -t bin/fleetctl
upx -q bin/fleetd
upx -t bin/fleetd
mv -v bin/fleetctl ${ROOTFS}/usr/bin/
mv -v bin/fleetd ${ROOTFS}/usr/bin/
