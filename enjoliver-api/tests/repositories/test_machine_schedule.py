import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from enjoliver.db import session_commit
from enjoliver.model import Base, Machine, MachineInterface, Schedule, ScheduleRoles
from enjoliver.repositories.machine_discovery import MachineDiscoveryRepository
from enjoliver.repositories.machine_schedule import MachineScheduleRepository

from tests.fixtures import posts


class TestMachineScheduleRepo(unittest.TestCase):
    engine = None  # type: Engine

    @classmethod
    def init_db(cls):
        if cls.engine is None:
            raise Exception('engine is None')

        Base.metadata.drop_all(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    @classmethod
    def setUpClass(cls):
        db_uri = 'postgresql+psycopg2://localhost/enjoliver_testing'
        cls.engine = create_engine(db_uri)
        cls.sess_maker = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.init_db()

    def test_one_machine(self):
        mac = "00:00:00:00:00:00"
        with session_commit(sess_maker=self.sess_maker) as session:
            uuid = "b7f5f93a-b029-475f-b3a4-479ba198cb8a"
            machine = Machine(uuid=uuid)
            session.add(machine)
            machine_id = session.query(Machine).filter(Machine.uuid == uuid).first().id
            session.add(
                MachineInterface(machine_id=machine_id, mac=mac, netmask=1, ipv4="10.10.10.10", cidrv4="127.0.0.1/8",
                                 as_boot=True, gateway="1.1.1.1", name="lol"))
            session.commit()

        ms = MachineScheduleRepository(sess_maker=self.sess_maker)
        ret = ms.get_available_machines()
        self.assertEqual(1, len(ret))

    def test_one_machine_scheduled_node(self):
        mac = "00:00:00:00:00:00"
        with session_commit(sess_maker=self.sess_maker) as session:
            uuid = "b7f5f93a-b029-475f-b3a4-479ba198cb8a"
            machine = Machine(uuid=uuid)
            session.add(machine)
            machine_id = session.query(Machine).filter(Machine.uuid == uuid).first().id
            session.add(
                MachineInterface(machine_id=machine_id, mac=mac, netmask=1, ipv4="10.10.10.10", cidrv4="127.0.0.1/8",
                                 as_boot=True, gateway="1.1.1.1", name="lol"))
            session.add(Schedule(
                machine_id=machine_id,
                role=ScheduleRoles.kubernetes_node))
            session.commit()

        ms = MachineScheduleRepository(sess_maker=self.sess_maker)
        ret = ms.get_available_machines()
        self.assertEqual(0, len(ret))
        ret = ms.get_roles_by_mac_selector(mac)
        self.assertEqual([ScheduleRoles.kubernetes_node], ret)
        ret = ms.get_machines_by_roles(ScheduleRoles.etcd_member, ScheduleRoles.kubernetes_control_plane)
        self.assertEqual(0, len(ret))
        ret = ms.get_machines_by_roles(ScheduleRoles.kubernetes_node)
        self.assertEqual(1, len(ret))
        ret = ms.get_machines_by_roles(ScheduleRoles.etcd_member)
        self.assertEqual(0, len(ret))
        ret = ms.get_machines_by_roles(ScheduleRoles.kubernetes_control_plane)
        self.assertEqual(0, len(ret))

    def test_one_machine_scheduled_cp(self):
        mac = "00:00:00:00:00:00"
        with session_commit(sess_maker=self.sess_maker) as session:
            uuid = "b7f5f93a-b029-475f-b3a4-479ba198cb8a"
            machine = Machine(uuid=uuid)
            session.add(machine)
            machine_id = session.query(Machine).filter(Machine.uuid == uuid).first().id
            session.add(
                MachineInterface(machine_id=machine_id, mac=mac, netmask=1, ipv4="10.10.10.10", cidrv4="127.0.0.1/8",
                                 as_boot=True, gateway="1.1.1.1", name="lol"))
            session.add(Schedule(
                machine_id=machine_id,
                role=ScheduleRoles.etcd_member))
            session.add(Schedule(
                machine_id=machine_id,
                role=ScheduleRoles.kubernetes_control_plane))
            session.commit()

        ms = MachineScheduleRepository(sess_maker=self.sess_maker)
        ret = ms.get_available_machines()
        self.assertEqual(0, len(ret))

        ret = ms.get_roles_by_mac_selector(mac)
        self.assertEqual([ScheduleRoles.etcd_member, ScheduleRoles.kubernetes_control_plane], ret)

        ret = ms.get_machines_by_roles(ScheduleRoles.etcd_member, ScheduleRoles.kubernetes_control_plane)
        self.assertEqual(1, len(ret))

        ret = ms.get_machines_by_roles(ScheduleRoles.kubernetes_node)
        self.assertEqual(0, len(ret))

        ret = ms.get_machines_by_roles(ScheduleRoles.etcd_member)
        self.assertEqual(1, len(ret))

        ret = ms.get_machines_by_roles(ScheduleRoles.kubernetes_control_plane)
        self.assertEqual(1, len(ret))

    def test_one_machine_scheduled_etcd(self):
        mac = "00:00:00:00:00:00"
        with session_commit(sess_maker=self.sess_maker) as session:
            uuid = "b7f5f93a-b029-475f-b3a4-479ba198cb8a"
            machine = Machine(uuid=uuid)
            session.add(machine)
            machine_id = session.query(Machine).filter(Machine.uuid == uuid).first().id
            session.add(
                MachineInterface(machine_id=machine_id, mac=mac, netmask=1, ipv4="10.10.10.10", cidrv4="127.0.0.1/8",
                                 as_boot=True, gateway="1.1.1.1", name="lol"))
            session.add(Schedule(
                machine_id=machine_id,
                role=ScheduleRoles.etcd_member))
            session.commit()

        ms = MachineScheduleRepository(sess_maker=self.sess_maker)
        ret = ms.get_available_machines()
        self.assertEqual(0, len(ret))

        ret = ms.get_roles_by_mac_selector(mac)
        self.assertEqual([ScheduleRoles.etcd_member], ret)

        ret = ms.get_machines_by_roles(ScheduleRoles.etcd_member, ScheduleRoles.kubernetes_control_plane)
        self.assertEqual(0, len(ret))

        ret = ms.get_machines_by_roles(ScheduleRoles.kubernetes_node)
        self.assertEqual(0, len(ret))

        ret = ms.get_machines_by_roles(ScheduleRoles.etcd_member)
        self.assertEqual(1, len(ret))

        ret = ms.get_machines_by_roles(ScheduleRoles.kubernetes_control_plane)
        self.assertEqual(0, len(ret))

    def test_one_machine_discovery(self):
        mds = MachineDiscoveryRepository(sess_maker=self.sess_maker)
        mds.upsert(posts.M01)
        ms = MachineScheduleRepository(sess_maker=self.sess_maker)
        ret = ms.get_available_machines()
        self.assertEqual(1, len(ret))

    def test_two_machine_discovery(self):
        mds = MachineDiscoveryRepository(sess_maker=self.sess_maker)
        mds.upsert(posts.M01)
        mds.upsert(posts.M02)
        ms = MachineScheduleRepository(sess_maker=self.sess_maker)
        ret = ms.get_available_machines()
        self.assertEqual(2, len(ret))

    def test_two_machine_discovery_idemp(self):
        mds = MachineDiscoveryRepository(sess_maker=self.sess_maker)
        mds.upsert(posts.M01)
        mds.upsert(posts.M02)
        ms = MachineScheduleRepository(sess_maker=self.sess_maker)
        ret = ms.get_available_machines()
        self.assertEqual(2, len(ret))
        ms = MachineScheduleRepository(sess_maker=self.sess_maker)
        ret = ms.get_available_machines()
        self.assertEqual(2, len(ret))

    def test_machine_without_role(self):
        mds = MachineDiscoveryRepository(sess_maker=self.sess_maker)
        mds.upsert(posts.M01)
        mds.upsert(posts.M02)
        ms = MachineScheduleRepository(sess_maker=self.sess_maker)
        for role in ScheduleRoles.roles:
            ret = ms.get_machines_by_role(role)
            self.assertEqual(0, len(ret))

    def test_machine_without_role2(self):
        mds = MachineDiscoveryRepository(sess_maker=self.sess_maker)
        mds.upsert(posts.M01)
        mds.upsert(posts.M02)
        ms = MachineScheduleRepository(sess_maker=self.sess_maker)
        ret = ms.get_all_schedules()
        self.assertEqual(0, len(ret))

    def test_machine_without_role3(self):
        mds = MachineDiscoveryRepository(sess_maker=self.sess_maker)
        mds.upsert(posts.M01)
        mds.upsert(posts.M02)
        ms = MachineScheduleRepository(sess_maker=self.sess_maker)
        ret = ms.get_roles_by_mac_selector(posts.M01["boot-info"]["mac"])
        self.assertEqual(0, len(ret))

    def test_machine_without_role4(self):
        mds = MachineDiscoveryRepository(sess_maker=self.sess_maker)
        mds.upsert(posts.M01)
        mds.upsert(posts.M02)
        ms = MachineScheduleRepository(sess_maker=self.sess_maker)
        for role in ScheduleRoles.roles:
            ret = ms.get_role_ip_list(role)
            self.assertEqual(0, len(ret))

    def test_one_machine_to_schedule(self):
        mac = "00:00:00:00:00:00"
        with session_commit(sess_maker=self.sess_maker) as session:
            uuid = "b7f5f93a-b029-475f-b3a4-479ba198cb8a"
            machine = Machine(uuid=uuid)
            session.add(machine)
            machine_id = session.query(Machine).filter(Machine.uuid == uuid).first().id
            session.add(
                MachineInterface(machine_id=machine_id, mac=mac, netmask=1, ipv4="10.10.10.10", cidrv4="127.0.0.1/8",
                                 as_boot=True, gateway="1.1.1.1", name="lol"))

            session.commit()

        ms = MachineScheduleRepository(sess_maker=self.sess_maker)
        data = {
            "roles": ["kubernetes-control-plane", "etcd-member"],
            "selector": {
                "mac": mac
            }
        }
        s = ms.get_all_schedules()
        self.assertEqual(0, len(s))

        ms.create_schedule(data)
        ms.create_schedule(data)
        s = ms.get_all_schedules()
        self.assertEqual(1, len(s))

        s = ms.get_machines_by_roles(*["kubernetes-control-plane", "etcd-member"])
        self.assertEqual(1, len(s))

        s = ms.get_machines_by_roles("kubernetes-control-plane")
        self.assertEqual(1, len(s))
