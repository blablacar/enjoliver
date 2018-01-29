# Enjoliver achitecture overview


## Discovery

The discovery allows to boot in memory CoreOS instances to proceed of:

1) sending the facts of the machine (MAC address, IP address, ...)
2) fetch his role
3) disk installation


For matchbox, the discovery profile has one group without any selector.

In this case, all un-selected machines will match this profile by default.
This profile has one associated group, with 2 metadata entries:

1) api uri
2) ssh-key

How the discovery process works:

![machine-boot](machine-boot.jpg)


## Rolling Updates
During the lifecycle of the Kubernetes cluster, rolling updates are **fast** and fully controlled.
* The rolling update of the configuration changes are granted by Enjoliver API `/lifecycle/rolling/mac=00:01:02:03:04:05`
* The semaphore is managed by locksmith.
* The Ignition is applied after a fast systemd-kexec or normal reboot

Each node can be re-installed and re-join the cluster.


Each minute, every machine reports the content of `/usr/share/oem/coreos-install.json` to the enjoliver API `lifecycle/ignition/`
Enjoliver will query matchbox and compare the content of the current ignition report and the desired ignition provided by matchbox.
The result will be stored in the database and returned to the machine.

If the state is outdated, the machine will ask its rollingUpdate strategy:
* disable : unset
* kexec
* reboot
* poweroff

If a strategy is returned, the machine try to takes a lock in locksmith and
proceeds to tear down the machine.
The tear down proceed to drain the kubernetes node. Its disables the scheduling
of the node.

When the machine goes back, the ready process starts:
* check etcd-vault
* check etcd-kubernetes
* check etcd-fleet
* check kubernetes cluster trough the local kube-apiserver
* check the kubelet
* check if the node is registered in fleet machines
    * trough local etcd-fleet
    * over remotes etcd-fleet
* uncordon the kubernetes node
* release the lock in locksmith
