import copy
import os
import unittest

import sys
import time

from enjoliver import k8s_2t

try:
    import kvm_player
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import kvm_player


@unittest.skipIf(os.getenv("DISK_OK") is None, "Skip because DISK_OK=")
class TestKVMK8sEnjolivageDiskLifecycle(kvm_player.KernelVirtualMachinePlayer):
    @classmethod
    def setUpClass(cls):
        cls.running_requirements()
        cls.set_rack0()
        cls.set_acserver()
        cls.set_api()
        cls.set_matchbox()
        cls.set_dnsmasq()
        cls.pause(cls.wait_setup_teardown)


# @unittest.skip("")
class TestKVMK8SEnjolivageDiskLifecycleLifecycle0(TestKVMK8sEnjolivageDiskLifecycle):
    # @unittest.skip("just skip")
    def test_00(self):
        self.assertEqual(self.fetch_discovery(), [])
        nb_node = 3
        marker = "plans-%s-%s" % (TestKVMK8sEnjolivageDiskLifecycle.__name__.lower(), self.test_00.__name__)
        nodes = ["%s-%d" % (marker, i) for i in range(nb_node)]
        ignitions = {
            "discovery": marker,
            "etcd_member_kubernetes_control_plane": "%s-%s" % (marker, "etcd-member-control-plane"),
            "kubernetes_nodes": "%s-%s" % (marker, "k8s-node"),
        }
        k8s_2t.EC.lldp_image_url = ""
        plan_k8s_2t = k8s_2t.Kubernetes2Tiers(
            ignitions,
            matchbox_path=self.test_matchbox_path,
            api_uri=self.api_uri,
            extra_selectors=self.ec.extra_selectors,
        )

        for i in range(nb_node):
            machine_marker = "%s-%d" % (marker, i)
            self.clean_up_virtual_machine(machine_marker)
        try:
            for i, m in enumerate(nodes):
                virt_install = self.create_virtual_machine(m, nb_node, disk_gb=10)
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.testing_sleep_seconds)

            time.sleep(self.testing_sleep_seconds * self.testing_sleep_seconds)

            for i in range(120):
                if plan_k8s_2t.apply() == nb_node:
                    break
                time.sleep(self.testing_sleep_seconds)

            time.sleep(self.testing_sleep_seconds * self.testing_sleep_seconds + (nb_node * 10))

            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)

            iterations = nb_node * 3 + 2

            for i in range(iterations):
                # 3 loops by node
                # 1) setup
                # 2) reboot
                # 3) destroy -> setup
                # 4) update
                time.sleep(self.testing_sleep_seconds * self.testing_sleep_seconds)

                self.etcd_member_len(plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3],
                                     plan_k8s_2t._sch_k8s_control_plane.expected_nb,
                                     self.ec.vault_etcd_client_port, tries=60, verify=False)
                self.etcd_endpoint_health(plan_k8s_2t.kubernetes_control_plane_ip_list, self.ec.vault_etcd_client_port,
                                          verify=False, tries=60)

                if i == 0:
                    self.vault_self_certs(plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3],
                                          self.ec.vault_etcd_client_port)
                    self.vault_verifing_issuing_ca(plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3],
                                                   self.ec.vault_etcd_client_port)
                    self.vault_issue_app_certs(plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3],
                                               self.ec.vault_etcd_client_port)
                    self.save_unseal_key(plan_k8s_2t.kubernetes_control_plane_ip_list)

                self.unseal_all_vaults(plan_k8s_2t.kubernetes_control_plane_ip_list, self.ec.vault_etcd_client_port)

                self.etcd_member_len(
                    plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3], plan_k8s_2t._sch_k8s_control_plane.expected_nb,
                    self.ec.kubernetes_etcd_client_port, certs_name="etcd-kubernetes_client")
                self.etcd_member_len(
                    plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3], plan_k8s_2t._sch_k8s_control_plane.expected_nb,
                    self.ec.fleet_etcd_client_port, certs_name="etcd-fleet_client")

                self.etcd_endpoint_health(
                    plan_k8s_2t.kubernetes_control_plane_ip_list, self.ec.kubernetes_etcd_client_port,
                    certs_name="etcd-kubernetes_client")
                self.etcd_endpoint_health(
                    plan_k8s_2t.kubernetes_control_plane_ip_list + plan_k8s_2t.kubernetes_nodes_ip_list,
                    self.ec.fleet_etcd_client_port, certs_name="etcd-fleet_client")

                self.kube_apiserver_health(plan_k8s_2t.kubernetes_control_plane_ip_list)
                self.kubernetes_node_nb(plan_k8s_2t.etcd_member_ip_list[i % 3], nb_node)

                if i == 0:
                    self.create_tiller(plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3])
                self.healthz_enjoliver_agent(
                    plan_k8s_2t.kubernetes_control_plane_ip_list + plan_k8s_2t.kubernetes_nodes_ip_list)

                ips = copy.deepcopy(plan_k8s_2t.kubernetes_control_plane_ip_list + plan_k8s_2t.kubernetes_nodes_ip_list)
                self.pod_tiller_is_running(plan_k8s_2t.kubernetes_control_plane_ip_list[i % 3])

                if i == 0:
                    for etcd in ["vault", "kubernetes"]:
                        self.create_helm_etcd_backup(plan_k8s_2t.etcd_member_ip_list[i % 3], etcd)
                    for chart in ["heapster", "node-exporter", "prometheus"]:
                        self.create_helm_by_name(plan_k8s_2t.etcd_member_ip_list[0], chart)

                self.daemonset_node_exporter_are_running(ips)

                # takes about one minute to run the cronjob so we postpone this check after the tiller ops
                for etcd in ["vault", "kubernetes"]:
                    self.etcd_backup_done(plan_k8s_2t.etcd_member_ip_list[i % 3], etcd)

                machine_marker = "%s-%d" % (marker, i % 3)
                destroy, vol_delete, vol_create, start = \
                    ["virsh", "destroy", "%s" % machine_marker], \
                    ["virsh", "vol-delete", "%s.qcow2" % machine_marker, "--pool", "default"], \
                    ["virsh", "vol-create-as", "--name", "%s.qcow2" % machine_marker,
                     "--pool", "default", "--capacity", "11GB", "--format", "qcow2"], \
                    ["virsh", "start", "%s" % machine_marker]

                if i == iterations - 2:
                    self.ec.kubernetes_apiserver_insecure_port = 8181
                    self.replace_ignition_metadata("kubernetes_apiserver_insecure_port",
                                                   self.ec.kubernetes_apiserver_insecure_port)

                    for k in range(nb_node):
                        time.sleep(self.testing_sleep_seconds * 15)
                        self.unseal_all_vaults(plan_k8s_2t.kubernetes_control_plane_ip_list,
                                               self.ec.vault_etcd_client_port)

                    continue

                self.virsh(destroy)
                time.sleep(1)
                if i + 1 > nb_node * 2:
                    self.virsh(vol_delete)
                    self.virsh(vol_create)
                self.virsh(start)

            self.write_ending(marker)

        finally:
            try:
                if os.getenv("TEST"):
                    self.iteractive_usage(
                        api_server_ip=plan_k8s_2t.kubernetes_control_plane_ip_list[0],
                        # fns=[plan_k8s_2t.apply]
                    )
            finally:
                for i in range(nb_node):
                    machine_marker = "%s-%d" % (marker, i)
                    self.clean_up_virtual_machine(machine_marker)


if __name__ == "__main__":
    unittest.main(defaultTest=os.getenv("TEST"))
