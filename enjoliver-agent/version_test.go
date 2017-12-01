package main

import (
	"testing"
)

func TestGetStringInTable(t *testing.T) {
	rktOutput := `v Version: 1.25.0
appc Version: 0.8.10
Go Version: go1.7.4
Go OS/Arch: linux/amd64
Features: -TPM +SDJOURNAL
`
	v, err := getStringInTable(rktOutput, rktVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "1.25.0" {
		t.Errorf("fail to get version: %s", v)
	}

	hyperkubeOutput := "Kubernetes v1.6.2+477efc3\n"
	v, err = getStringInTable(hyperkubeOutput, hyperkubeVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "v1.6.2+477efc3" {
		t.Errorf("fail to get version: %s", v)
	}

	etcdOutput := `etcd Version: 3.2.5
	Git SHA: d0d1a87
	Go Version: go1.8.3
	Go OS/Arch: linux/amd64
`
	v, err = getStringInTable(etcdOutput, etcdVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "3.2.5" {
		t.Errorf("fail to get version: %s", v)
	}

	ipOutput := "ip utility, iproute2-ss151103\n"
	v, err = getStringInTable(ipOutput, iproute2Version)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "iproute2-ss151103" {
		t.Errorf("fail to get version: %s", v)
	}

	vaultOutput := "Vault v0.8.0 ('af63d879130d2ee292f09257571d371100a513eb')\n"
	v, err = getStringInTable(vaultOutput, vaultVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "v0.8.0" {
		t.Errorf("fail to get version: %s", v)
	}

	sdOutput := `systemd 233
	+PAM +AUDIT +SELINUX +IMA -APPARMOR +SMACK -SYSVINIT +UTMP +LIBCRYPTSETUP +GCRYPT -GNUTLS -ACL +XZ -LZ4 +SECCOMP +BLKID -ELFUTILS +KMOD -IDN default-hierarchy=legacy
`
	v, err = getStringInTable(sdOutput, systemdVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "233" {
		t.Errorf("fail to get version: %s", v)
	}

	unameOutput := "4.11.9-coreos\n"
	v, err = getStringInTable(unameOutput, kernelVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "4.11.9-coreos" {
		t.Errorf("fail to get version: %s", v)
	}

	fleetOutput := "fleetd version v1.0.0\n"
	v, err = getStringInTable(fleetOutput, fleetVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "v1.0.0" {
		t.Errorf("fail to get version: %s", v)
	}

	haproxyOutput := `HA-Proxy version 1.7.5 2017/04/03
Copyright 2000-2017 Willy Tarreau <willy@haproxy.org>

`
	v, err = getStringInTable(haproxyOutput, haproxyVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "1.7.5" {
		t.Errorf("fail to get version: %s", v)
	}

	socatOutput := `[64604.961670] socat[18]: socat by Gerhard Rieger and contributors - see www.dest-unreach.org
[64604.962631] socat[18]: socat version 1.7.3.2 on Dec  1 2017 13:26:02
[64604.963345] socat[18]:    running on Linux version #1 SMP Wed Nov 8 08:09:32 UTC 2017, release 4.14.0-rc8-coreos, machine x86_64
[64604.965175] socat[18]: features:
[64604.965761] socat[18]:   #define WITH_STDIO 1
[64604.966496] socat[18]:   #define WITH_FDNUM 1
[64604.966977] socat[18]:   #define WITH_FILE 1
[64604.967372] socat[18]:   #define WITH_CREAT 1
[64604.967829] socat[18]:   #define WITH_GOPEN 1
[64604.968578] socat[18]:   #define WITH_TERMIOS 1
[64604.969497] socat[18]:   #define WITH_PIPE 1
[64604.971745] socat[18]:   #define WITH_UNIX 1
[64604.972750] socat[18]:   #define WITH_ABSTRACT_UNIXSOCKET 1
[64604.973593] socat[18]:   #define WITH_IP4 1
[64604.974709] socat[18]:   #define WITH_IP6 1
[64604.976783] socat[18]:   #define WITH_RAWIP 1
[64604.977409] socat[18]:   #define WITH_GENERICSOCKET 1
[64604.979955] socat[18]:   #define WITH_INTERFACE 1
[64604.980049] socat[18]:   #define WITH_TCP 1
[64604.980251] socat[18]:   #define WITH_UDP 1
[64604.980338] socat[18]:   #define WITH_SCTP 1
[64604.980398] socat[18]:   #define WITH_LISTEN 1
[64604.980455] socat[18]:   #define WITH_SOCKS4 1
[64604.980524] socat[18]:   #define WITH_SOCKS4A 1
[64604.980822] socat[18]:   #define WITH_PROXY 1
[64604.981180] socat[18]:   #define WITH_SYSTEM 1
[64604.981510] socat[18]:   #define WITH_EXEC 1
[64604.982283] socat[18]:   #undef WITH_READLINE
[64604.983123] socat[18]:   #define WITH_TUN 1
[64604.983673] socat[18]:   #define WITH_PTY 1
[64604.985334] socat[18]:   #undef WITH_OPENSSL
[64604.987989] socat[18]:   #undef WITH_FIPS
[64604.988508] socat[18]:   #undef WITH_LIBWRAP
[64604.988739] socat[18]:   #define WITH_SYCLS 1
[64604.989410] socat[18]:   #define WITH_FILAN 1
[64604.989995] socat[18]:   #define WITH_RETRY 1
[64604.993234] socat[18]:   #define WITH_MSGLEVEL 0 /*debug*/
`
	v, err = getStringInTable(socatOutput, socatVersion)
	if err != nil {
		t.Errorf(err.Error())
	}
	if v != "1.7.3.2" {
		t.Errorf("fail to get socat version: %s", v)
	}
}
