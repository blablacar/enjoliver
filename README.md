# Enjoliver
[![Build Status](https://travis-ci.org/blablacar/enjoliver.svg?branch=master)](https://travis-ci.org/blablacar/enjoliver)

Network boot servers and provision a Container Linux OS running a Kubernetes
cluster.


## Description


Enjoliver is a framework that aim to deploy and maintain an usable Kubernetes
cluster from a bare-metal environment.

Enjoliver only supports `rkt` as the kubelet runtime for now.

Typical use-cases are :
  - spawn a kubernetes cluster in a new datacenter ;
  - test a custom patch on kubernetes ;


## Overview

![enjoliver-archi](docs/enjoliver-architecture.jpg)

**enjoliver-api** the engine that orchestrate the installation workflow. It
reponds to ipxe requests, serves ignition files according to the machine
profile, and centralize the update logic.

**matchbox** matches servers with and OS version and ignition config.

**enjoliver-ui** is an UI that helps you manage the lifcycle of the bare-metal.

**enjoliver-testsuite** is an end-to-end testsuite for the whole framework.
It boots a fleet of kvm virtual machines into th complete installation cycle
an runs tests on each components.


## Documentation

### Enjoliver Engine
    * Discovery Topology
    * Scheduling of Kubernetes roles
    * Lifecycle management

[Enjoliver architecture overview](docs/enjoliver-architecture.md)
[How to run enjoliver in production](docs/usage-production.md)



## Configuration of Kubernetes cluster
    * control plane
    * node

[Kubernetes Cluster Architecture](docs/kubernetes-architecture.md)


## Kubernetes cluster for development usage
ready to use with samples:

    * Helm / Tiller
    * Heapster
    * Kubernetes Dashboard
    * Kubernetes state metrics
    * Node exporter for Prometheus
    * Prometheus
    * Vault UI
    * CronJobs for etcd3 backups

[How to setup a development environment](docs/usage-development.md)


## End-to-end testing with enjoliver
    * follow any associated releases
    * features, bug fix testing in cluster

[How to run end-to-end tests](docs/usage-end-to-end.md)



### Stuff we use

* [Container Linux](https://coreos.com/releases)
* [etcd](https://github.com/coreos/etcd/releases)
* [cni](https://github.com/containernetworking/cni/releases)
* [rkt](https://github.com/rkt/rkt/releases)
* [kubernetes](https://github.com/kubernetes/kubernetes/releases)
* [vault](https://github.com/hashicorp/vault/releases)
* [fleet](https://github.com/coreos/fleet/releases)

