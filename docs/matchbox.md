# Matchbox

[Official project](https://github.com/coreos/matchbox#matchbox)

Enjoliver use 3 profiles in matchbox
1) discovery
2) etcd-member-kubernetes-control-plane
2) kubernetes-node

## etcd-member-kubernetes-control-plane

This role is for:
1) etcd members
    * vault
    * fleet
    * kubernetes
2) vault
3) kube-{apiserver, controller-manager, scheduler}

This role need to be bootstrapped as 3, 5, ... instances and is needed by all the other nodes.

To solve this problem, the Enjoliver Scheduler will apply the roles only if the required number of instances are available.

So, if the cluster size is 5, the first 5 instances in discovery will get this role.


## kubernetes-node

This role is a standard worker (Kubernetes node)

All additional nodes over the wanted **etcd-member-kubernetes-control-plane** requirements will become **kubernetes-node**

