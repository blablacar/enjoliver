import os
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase

from enjoliver import generator


class GenerateGroupTestCase(TestCase):
    api_uri = None
    test_matchbox_path = None
    test_resources_path = None
    tests_path = None

    @classmethod
    def setUpClass(cls):
        cls.tests_path = mkdtemp(dir='/tmp')
        cls.test_matchbox_path = os.path.join(cls.tests_path, 'test_matchbox')
        cls.test_resources_path = os.path.join(cls.tests_path, 'test_resources')

        os.mkdir(cls.test_matchbox_path)
        os.mkdir(cls.test_resources_path)
        os.mkdir(os.path.join(cls.test_matchbox_path, 'groups'))

        cls.api_uri = "http://127.0.0.1:5000"

    @classmethod
    def tearDownClass(cls):
        rmtree(cls.tests_path)


class TestGenerateGroups(GenerateGroupTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.gen = generator.GenerateGroup(
            api_uri=cls.api_uri,
            _id="etcd-proxy",
            name="etcd-proxy",
            profile="TestGenerateProfiles",
            matchbox_path=cls.test_matchbox_path
        )
        cls.gen.profiles_path = cls.test_resources_path

    def test_instantiate_generate_group_with_incorrect_parameters(self):
        with self.assertRaises(TypeError):
            generator.GenerateGroup()

    def test_instantiate_generate_group_with_non_existing_matchbox_path(self):
        with self.assertRaises(OSError):
            generator.GenerateGroup(
                api_uri='foobar',
                _id='foo',
                name='foo-bar',
                profile='foo-bar-baz',
                matchbox_path='/foo/bar'
            )

    def test_instantiate_generate_group(self):
        sandbox = mkdtemp(dir='/tmp')
        os.mkdir(os.path.join(sandbox, 'groups'))

        generator.GenerateGroup(
            api_uri='foobar',
            _id='foo',
            name='foo-bar',
            profile='foo-bar-baz',
            matchbox_path=sandbox
        )
        rmtree(sandbox)

    def test_00_uri(self):
        ip = self.gen.api_uri
        self.assertIsNotNone(ip)

    def test_01_metadata(self):
        expect = {'etcd_initial_cluster': '',
                  'api_uri': '%s' % self.gen.api_uri,
                  'ssh_authorized_keys': []}

        self.gen._metadata()
        self.assertEqual(expect['api_uri'], self.gen._target_data["metadata"]["api_uri"])

    def test_990_generate(self):
        expect = {
            'profile': 'etcd-proxy.yaml',
            'metadata': {
                'api_uri': '%s' % self.gen.api_uri,
                'ssh_authorized_keys': []
            },
            'id': 'etcd-proxy',
            'name': 'etcd-proxy'
        }
        new = generator.GenerateGroup(
            api_uri=self.api_uri,
            _id="etcd-proxy",
            name="etcd-proxy",
            profile="etcd-proxy.yaml",
            matchbox_path=self.test_matchbox_path
        )
        result = new.generate()
        self.assertEqual(expect["profile"], result["profile"])
        self.assertEqual(expect["id"], result["id"])
        self.assertEqual(expect["name"], result["name"])
        self.assertEqual(expect["metadata"]["api_uri"], result["metadata"]["api_uri"])

    def test_991_dump(self):
        _id = "etcd-test-%s" % self.test_991_dump.__name__
        new = generator.GenerateGroup(
            api_uri=self.api_uri,
            _id=_id,
            name="etcd-test",
            profile="etcd-test.yaml",
            matchbox_path=self.test_matchbox_path
        )
        self.assertTrue(new.dump())
        self.assertTrue(os.path.isfile("%s/groups/%s.json" % (self.test_matchbox_path, _id)))

        self.assertFalse(new.dump())
        self.assertTrue(os.path.isfile("%s/groups/%s.json" % (self.test_matchbox_path, _id)))

        new = generator.GenerateGroup(
            api_uri=self.api_uri,
            _id=_id,
            name="etcd-test",
            profile="etcd-test.yaml",
            matchbox_path=self.test_matchbox_path,
            selector={"one": "selector"}
        )
        self.assertTrue(new.dump())
        self.assertTrue(os.path.isfile("%s/groups/%s.json" % (self.test_matchbox_path, _id)))
        os.remove("%s/groups/%s.json" % (self.test_matchbox_path, _id))


class TestGenerateGroupsSelectorLower(GenerateGroupTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ["MATCHBOX_URI"] = "http://127.0.0.1:8080"
        os.environ["API_URI"] = "http://127.0.0.1:5000"
        cls.gen = generator.GenerateGroup(
            api_uri=cls.api_uri,
            _id="etcd-proxy",
            name="etcd-proxy",
            profile="TestGenerateProfiles",
            selector={"mac": "08:00:27:37:28:2e"},
            matchbox_path=cls.test_matchbox_path
        )

    def test_00_api_uri(self):
        ip = self.gen.api_uri
        self.assertIsNotNone(ip)

    def test_01_metadata(self):
        expect = {
            'api_uri': "%s" % self.gen.api_uri,
            'ssh_authorized_keys': []
        }
        self.gen._metadata()
        self.gen._target_data["metadata"]['ssh_authorized_keys'] = []
        self.assertEqual(expect, self.gen._target_data["metadata"])

    def test_02_selector(self):
        expect = {'mac': '08:00:27:37:28:2e'}
        self.gen._selector()
        self.assertEqual(expect, self.gen._target_data["selector"])

    def test_990_generate(self):
        expect = {
            'profile': 'etcd-proxy.yaml',
            'metadata': {
                'api_uri': self.gen.api_uri,
                'selector': {'mac': '08:00:27:37:28:2e'},
                'ssh_authorized_keys': []
            },
            'id': 'etcd-proxy',
            'name': 'etcd-proxy',
            'selector': {'mac': '08:00:27:37:28:2e'}
        }
        new = generator.GenerateGroup(
            api_uri=self.api_uri,
            _id="etcd-proxy", name="etcd-proxy", profile="etcd-proxy.yaml",
            selector={"mac": "08:00:27:37:28:2e"},
            matchbox_path=self.test_matchbox_path)
        result = new.generate()
        result["metadata"]['ssh_authorized_keys'] = []
        self.assertEqual(expect, result)

    def test_991_dump(self):
        _id = "etcd-test-%s" % self.test_991_dump.__name__
        new = generator.GenerateGroup(
            api_uri=self.api_uri,
            _id="%s" % _id, name="etcd-test", profile="etcd-test.yaml",
            matchbox_path=self.test_matchbox_path,
            selector={"mac": "08:00:27:37:28:2e"}
        )
        self.assertTrue(new.dump())
        self.assertTrue(os.path.isfile("%s/groups/%s.json" % (self.test_matchbox_path, _id)))
        os.remove("%s/groups/%s.json" % (self.test_matchbox_path, _id))


class TestGenerateGroupsSelectorUpper(GenerateGroupTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ["MATCHBOX_URI"] = "http://127.0.0.1:8080"
        os.environ["API_URI"] = "http://127.0.0.1:5000"
        cls.gen = generator.GenerateGroup(
            api_uri=cls.api_uri,
            _id="etcd-proxy",
            name="etcd-proxy",
            profile="TestGenerateProfiles",
            selector={"mac": "08:00:27:37:28:2E"},
            matchbox_path=cls.test_matchbox_path
        )

    def test_00_ip_address(self):
        ip = self.gen.api_uri
        self.assertIsNotNone(ip)

    def test_01_metadata(self):
        expect = {
            'api_uri': "%s" % self.gen.api_uri,
            'ssh_authorized_keys': []
        }
        self.gen._metadata()
        self.gen._target_data["metadata"]['ssh_authorized_keys'] = []
        self.assertEqual(expect, self.gen._target_data["metadata"])

    def test_02_selector(self):
        expect = {'mac': '08:00:27:37:28:2e'}
        self.gen._selector()
        self.assertEqual(expect, self.gen._target_data["selector"])

    def test_990_generate(self):
        expect = {
            'profile': 'etcd-proxy.yaml',
            'metadata': {
                'api_uri': "%s" % self.gen.api_uri,
                'selector': {'mac': '08:00:27:37:28:2e'},
                'ssh_authorized_keys': []
            },
            'id': 'etcd-proxy',
            'name': 'etcd-proxy',
            'selector': {'mac': '08:00:27:37:28:2e'}
        }
        new = generator.GenerateGroup(
            api_uri=self.api_uri, _id="etcd-proxy",
            name="etcd-proxy",
            profile="etcd-proxy.yaml",
            selector={"mac": "08:00:27:37:28:2e"},
            matchbox_path=self.test_matchbox_path
        )
        result = new.generate()
        result["metadata"]['ssh_authorized_keys'] = []
        self.assertEqual(expect, result)

    def test_991_dump(self):
        _id = "etcd-test-%s" % self.test_991_dump.__name__
        new = generator.GenerateGroup(
            api_uri=self.api_uri,
            _id="%s" % _id, name="etcd-test", profile="etcd-test.yaml",
            matchbox_path=self.test_matchbox_path,
            selector={"mac": "08:00:27:37:28:2e"}
        )
        new.dump()
        self.assertTrue(os.path.isfile("%s/groups/%s.json" % (self.test_matchbox_path, _id)))
        os.remove("%s/groups/%s.json" % (self.test_matchbox_path, _id))


class TestGenerateGroupsExtraMetadata(GenerateGroupTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ["MATCHBOX_URI"] = "http://127.0.0.1:8080"
        os.environ["API_URI"] = "http://127.0.0.1:5000"
        cls.gen = generator.GenerateGroup(
            api_uri=cls.api_uri,
            _id="etcd-proxy",
            name="etcd-proxy",
            profile="TestGenerateProfiles",
            selector={"mac": "08:00:27:37:28:2E"},
            metadata={"etcd_initial_cluster": "static0=http://192.168.1.1:2379",
                      "api_seed": "http://192.168.1.2:5000"},
            matchbox_path=cls.test_matchbox_path
        )

    def test_00_api_uri(self):
        ip = self.gen.api_uri
        self.assertIsNotNone(ip)

    def test_01_metadata(self):
        expect = {'etcd_initial_cluster': 'static0=http://192.168.1.1:2379',
                  'api_uri': "%s" % self.gen.api_uri,
                  'api_seed': 'http://192.168.1.2:5000',
                  'ssh_authorized_keys': []}
        self.gen._metadata()
        self.gen._target_data["metadata"]['ssh_authorized_keys'] = []
        self.assertEqual(expect, self.gen._target_data["metadata"])

    def test_02_selector(self):
        expect = {'mac': '08:00:27:37:28:2e'}
        self.gen._selector()
        self.assertEqual(expect, self.gen._target_data["selector"])

    def test_990_generate(self):
        expect = {
            'profile': 'etcd-proxy.yaml',
            'metadata': {
                'api_uri': "%s" % self.gen.api_uri,
                'selector': {'mac': '08:00:27:37:28:2e'},
                'ssh_authorized_keys': []
            },
            'id': 'etcd-proxy',
            'name': 'etcd-proxy',
            'selector': {'mac': '08:00:27:37:28:2e'}
        }
        new = generator.GenerateGroup(
            api_uri=self.api_uri,
            _id="etcd-proxy", name="etcd-proxy", profile="etcd-proxy.yaml",
            selector={"mac": "08:00:27:37:28:2e"},
            matchbox_path=self.test_matchbox_path
        )
        result = new.generate()
        result["metadata"]["ssh_authorized_keys"] = []
        self.assertEqual(expect, result)

    def test_991_dump(self):
        _id = "etcd-test-%s" % self.test_991_dump.__name__
        new = generator.GenerateGroup(
            api_uri=self.api_uri,
            _id="%s" % _id, name="etcd-test", profile="etcd-test.yaml",
            matchbox_path=self.test_matchbox_path,
            selector={"mac": "08:00:27:37:28:2e"}
        )
        self.assertTrue(new.dump())
        self.assertTrue(os.path.isfile("%s/groups/%s.json" % (self.test_matchbox_path, _id)))
        os.remove("%s/groups/%s.json" % (self.test_matchbox_path, _id))
        self.assertTrue(new.dump())
        for i in range(10):
            self.assertFalse(new.dump())
        new.api_uri = "http://google.com"
        self.assertTrue(new.dump())
        self.assertFalse(new.dump())
