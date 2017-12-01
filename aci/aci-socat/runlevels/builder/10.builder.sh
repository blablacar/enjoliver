#!/bin/bash

. /dgr/bin/functions.sh
isLevelEnabled "debug" && set -x
set -ex

set -o pipefail

# taken from : https://raw.githubusercontent.com/andrew-d/static-binaries/master/socat/build.sh

SOCAT_VERSION=${ACI_VERSION}
NCURSES_VERSION=6.0
READLINE_VERSION=7.0
OPENSSL_VERSION=1.1.0f

mkdir /build

cd /build
curl -LO http://invisible-mirror.net/archives/ncurses/ncurses-${NCURSES_VERSION}.tar.gz
tar zxvf ncurses-${NCURSES_VERSION}.tar.gz
cd ncurses-${NCURSES_VERSION} || exit 1
CC='/usr/bin/gcc -static' CFLAGS='-fPIC' ./configure \
	--disable-shared \
	--enable-static

cd /build
curl -LO ftp://ftp.cwru.edu/pub/bash/readline-${READLINE_VERSION}.tar.gz
tar xzvf readline-${READLINE_VERSION}.tar.gz
cd readline-${READLINE_VERSION}
CC='/usr/bin/gcc -static' CFLAGS='-fPIC' ./configure \
	--disable-shared \
	--enable-static
make -j$(nproc)

# Note that socat looks for readline in <readline/readline.h>, so we need
# that directory to exist.
ln -s /build/readline-${READLINE_VERSION} /build/readline

cd /build
curl -LO https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz
tar zxvf openssl-${OPENSSL_VERSION}.tar.gz
cd openssl-${OPENSSL_VERSION}
CC='/usr/bin/gcc -static' ./Configure no-shared no-async linux-x86_64
make -j$(nproc)

cd /build
curl -LO http://www.dest-unreach.org/socat/download/socat-${SOCAT_VERSION}.tar.gz
tar xzvf socat-${SOCAT_VERSION}.tar.gz
cd socat-${SOCAT_VERSION}
# Build
# NOTE: `NETDB_INTERNAL` is non-POSIX, and thus not defined by MUSL.
# We define it this way manually.
CC='/usr/bin/gcc -static' \
CFLAGS='-fPIC' \
CPPFLAGS="-I/build -I/build/openssl-${OPENSSL_VERSION}/include -DNETDB_INTERNAL=-1" \
LDFLAGS="-L/build/readline-${READLINE_VERSION} -L/build/ncurses-${NCURSES_VERSION}/lib -L/build/openssl-${OPENSSL_VERSION}" \
./configure
make -j$(nproc)
strip socat


mkdir -p ${ROOTFS}/usr/bin
mv socat ${ROOTFS}/usr/bin
