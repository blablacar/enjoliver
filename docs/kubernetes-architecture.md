# Kubernetes Cluster Architecture

![cp](docs/topology.jpg)

Kubernetes controller manager is deployed as *Pod* on each node of the control plane.
When the control plane runs the controller, the scheduler starts as a DaemonSet.

Vault, Kubernetes and Fleet have dedicated etcd clusters.

Vault pki backend secure the following components:

* etcd for fleet - API v2
    * peer
    * client
* etcd for kubernetes - API v3
    * peer
    * client
* kube-apiserver
    * x509 authentication for kubectl
    * service accounts
* kube-controller-manager
    * cluster signing key
* kubelet

Each etcd cluster supports automatic members replacement.
