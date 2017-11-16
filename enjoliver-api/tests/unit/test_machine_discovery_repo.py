import copy
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from enjoliver.db import session_commit
from enjoliver.model import MachineInterface, Machine, MachineDisk, Chassis, ChassisPort, Base
from enjoliver.repositories.machine_discovery import MachineDiscoveryRepository

from tests.fixtures import posts


class TestMachineStateRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_uri = 'postgresql+psycopg2://localhost/enjoliver_testing'
        cls.engine = create_engine(db_uri)
        cls.sess_maker = sessionmaker(bind=cls.engine)

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def test_bad_content(self):
        mdr = MachineDiscoveryRepository(self.sess_maker)
        with self.assertRaises(TypeError):
            mdr.upsert(dict())
        with self.assertRaises(TypeError):
            mdr.upsert({"lldp": ""})

    def test_no_machine(self):
        mdr = MachineDiscoveryRepository(self.sess_maker)
        mdr.upsert(posts.M01)

        with session_commit(sess_maker=self.sess_maker) as session:
            self.assertEqual(1, session.query(Machine).count())
            self.assertEqual(1, session.query(MachineInterface).count())
            self.assertEqual(1, session.query(MachineDisk).count())
            self.assertEqual(1, session.query(Chassis).count())
            self.assertEqual(1, session.query(ChassisPort).count())

    def test_no_machine_readd_same(self):
        mdr = MachineDiscoveryRepository(self.sess_maker)

        for i in range(3):
            mdr.upsert(posts.M01)

            with session_commit(sess_maker=self.sess_maker) as session:
                self.assertEqual(1, session.query(Machine).count())
                self.assertEqual(1, session.query(MachineInterface).count())
                self.assertEqual(1, session.query(MachineDisk).count())
                self.assertEqual(1, session.query(Chassis).count())
                self.assertEqual(1, session.query(ChassisPort).count())

    def test_no_machine_readd_disk_diff(self):
        mdr = MachineDiscoveryRepository(self.sess_maker)
        mdr.upsert(posts.M01)

        with session_commit(sess_maker=self.sess_maker) as session:
            self.assertEqual(1, session.query(Machine).count())
            self.assertEqual(1, session.query(MachineInterface).count())
            self.assertEqual(1, session.query(MachineDisk).count())
            self.assertEqual(1, session.query(Chassis).count())
            self.assertEqual(1, session.query(ChassisPort).count())

        with_new_disk = copy.deepcopy(posts.M01)
        with_new_disk["disks"].append({'size-bytes': 21474836481, 'path': '/dev/sdb'})
        mdr.upsert(with_new_disk)

        with session_commit(sess_maker=self.sess_maker) as session:
            self.assertEqual(1, session.query(Machine).count())
            self.assertEqual(1, session.query(MachineInterface).count())
            self.assertEqual(2, session.query(MachineDisk).count())
            self.assertEqual(1, session.query(Chassis).count())
            self.assertEqual(1, session.query(ChassisPort).count())

    def test_no_machine_remove_disks(self):
        mdr = MachineDiscoveryRepository(self.sess_maker)
        mdr.upsert(posts.M01)

        with session_commit(sess_maker=self.sess_maker) as session:
            self.assertEqual(1, session.query(Machine).count())
            self.assertEqual(1, session.query(MachineInterface).count())
            self.assertEqual(1, session.query(MachineDisk).count())
            self.assertEqual(1, session.query(Chassis).count())
            self.assertEqual(1, session.query(ChassisPort).count())

        without_disks = copy.deepcopy(posts.M01)
        without_disks["disks"] = None
        mdr.upsert(without_disks)

        with session_commit(sess_maker=self.sess_maker) as session:
            self.assertEqual(1, session.query(Machine).count())
            self.assertEqual(1, session.query(MachineInterface).count())
            self.assertEqual(0, session.query(MachineDisk).count())
            self.assertEqual(1, session.query(Chassis).count())
            self.assertEqual(1, session.query(ChassisPort).count())

    def test_fetch_one_machine(self):
        mdr = MachineDiscoveryRepository(self.sess_maker)
        mdr.upsert(posts.M01)

        disco = mdr.fetch_all_discovery()
        self.assertEqual(1, len(disco))
        self.assertEqual(posts.M01["boot-info"]["mac"], disco[0]["boot-info"]["mac"])
        self.assertEqual(posts.M01["boot-info"]["uuid"], disco[0]["boot-info"]["uuid"])
        self.assertEqual(posts.M01["disks"], disco[0]["disks"])
        self.assertEqual(1, len(disco[0]["interfaces"]))
        self.assertEqual(posts.M01["boot-info"]["mac"], disco[0]["interfaces"][0]["mac"])
        self.assertTrue(disco[0]["interfaces"][0]["as_boot"])
