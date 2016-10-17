import os
import subprocess
from unittest import TestCase

import re

from app import generate_profiles


class TestGenerateProfiles(TestCase):
    gen = generate_profiles.GenerateProfiles
    network_environment = "%s/misc/network-environment" % gen.bootcfg_path

    @classmethod
    def setUpClass(cls):
        subprocess.check_output(["make", "-C", cls.gen.project_path])
        cls.gen = generate_profiles.GenerateProfiles(
            _id="etcd-proxy", name="etcd-proxy", ignition_id="etcd-proxy")
        if os.path.isfile("%s" % cls.network_environment):
            os.remove("%s" % cls.network_environment)

    @classmethod
    def tearDownClass(cls):
        if os.path.isfile("%s" % cls.network_environment):
            os.remove("%s" % cls.network_environment)

    def test_00_ip_address(self):
        self.assertFalse(os.path.isfile("%s" % self.network_environment))
        ip = self.gen.ip_address
        match = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip)
        self.assertIsNotNone(match)
        self.assertTrue(os.path.isfile("%s" % self.network_environment))

    def test_01_boot(self):
        expect = {
            'kernel': '/assets/coreos/serve/coreos_production_pxe.vmlinuz',
            'initrd': ['/assets/coreos/serve/coreos_production_pxe_image.cpio.gz'],
            'cmdline':
                {
                    'coreos.autologin': '',
                    'coreos.first_boot': '',
                    'coreos.config.url': 'http://%s:8080/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp}' % self.gen.ip_address
                }
        }
        self.gen._boot()
        self.assertEqual(expect, self.gen.profile["boot"])

    def test_99_generate(self):
        expect = {
            "cloud_id": "",
            "boot": {
                "kernel": "/assets/coreos/serve/coreos_production_pxe.vmlinuz",
                "initrd": [
                    "/assets/coreos/serve/coreos_production_pxe_image.cpio.gz"
                ],
                "cmdline": {
                    "coreos.autologin": "",
                    "coreos.first_boot": "",
                    "coreos.config.url": "http://%s:8080/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp}" % self.gen.ip_address
                }
            },
            "id": "etcd-proxy",
            "ignition_id": "etcd-proxy",
            "name": "etcd-proxy"
        }
        new = generate_profiles.GenerateProfiles(
            _id="etcd-proxy", name="etcd-proxy", ignition_id="etcd-proxy")
        result = new.generate()
        self.assertEqual(expect, result)
