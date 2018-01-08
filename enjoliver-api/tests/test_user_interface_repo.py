import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from enjoliver.db import session_commit
from enjoliver.model import (
    Base,
    LifecycleRolling,
    Machine,
    MachineCurrentState,
    MachineDisk,
    MachineInterface,
    MachineStates,
    Schedule,
    ScheduleRoles,
)
from enjoliver.repositories import user_interface


class TestMachineStateRepo(unittest.TestCase):
    engine = None

    @classmethod
    def init_db(cls):
        if cls.engine is None:
            raise Exception('engine is None')

        Base.metadata.drop_all(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('postgresql+psycopg2://localhost/enjoliver_testing')
        cls.init_db()

        cls.sess_maker = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.init_db()

    def test_empty(self):
        ui = user_interface.UserInterfaceRepository(sess_maker=self.sess_maker)
        self.assertEqual([], ui.get_machines_overview())

    def test_one_machine_with_only_interfaces(self):
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

        expect = list()
        expect.append(
            {
                'CIDR': '127.0.0.1/8',
                'LastReport': None,
                'UpdateStrategy': 'Disable',
                'LastChange': None,
                'MAC': '00:00:00:00:00:00',
                'UpToDate': None,
                'FQDN': None,
                'DiskProfile': 'inMemory',
                'LastState': None,
                'Roles': ''}
        )
        ui = user_interface.UserInterfaceRepository(sess_maker=self.sess_maker)
        self.assertCountEqual(expect, ui.get_machines_overview())

    def test_one_machine_full(self):
        mac = "00:00:00:00:00:00"

        with session_commit(sess_maker=self.sess_maker) as session:
            uuid = "b7f5f93a-b029-475f-b3a4-479ba198cb8a"
            machine = Machine(uuid=uuid)
            session.add(machine)
            machine_id = session.query(Machine).filter(Machine.uuid == uuid).first().id
            session.add(
                MachineInterface(machine_id=machine_id, mac=mac, netmask=1, ipv4="10.10.10.10", cidrv4="127.0.0.1/8",
                                 as_boot=True, gateway="1.1.1.1", name="lol"))
            session.add(
                MachineDisk(path="/dev/sda", size=1024 * 1024 * 1024, machine_id=machine_id)
            )
            session.add(
                MachineCurrentState(machine_id=machine_id, machine_mac=mac, state_name=MachineStates.discovery)
            )
            session.commit()

        expect = list()
        expect.append(
            {
                'CIDR': '127.0.0.1/8',
                'LastReport': None,
                'UpdateStrategy': 'Disable',
                'LastChange': None,
                'MAC': '00:00:00:00:00:00',
                'UpToDate': None,
                'FQDN': None,
                'DiskProfile': 'S',
                'LastState': MachineStates.discovery,
                'Roles': ''}
        )
        ui = user_interface.UserInterfaceRepository(sess_maker=self.sess_maker)
        data = ui.get_machines_overview()
        self.assertCountEqual(expect, data)

    def test_one_machine_full_scheduled(self):
        mac = "00:00:00:00:00:00"

        with session_commit(sess_maker=self.sess_maker) as session:
            uuid = "b7f5f93a-b029-475f-b3a4-479ba198cb8a"
            machine = Machine(uuid=uuid)
            session.add(machine)
            machine_id = session.query(Machine).filter(Machine.uuid == uuid).first().id
            session.add(
                MachineInterface(machine_id=machine_id, mac=mac, netmask=1, ipv4="10.10.10.10", cidrv4="127.0.0.1/8",
                                 as_boot=True, gateway="1.1.1.1", name="lol"))
            session.add(
                MachineDisk(path="/dev/sda", size=1024 * 1024 * 1024, machine_id=machine_id)
            )
            session.add(
                MachineCurrentState(machine_id=machine_id, machine_mac=mac, state_name=MachineStates.discovery)
            )
            session.add(
                Schedule(machine_id=machine_id, role=ScheduleRoles.kubernetes_control_plane)
            )
            session.commit()

        expect = list()
        expect.append(
            {
                'CIDR': '127.0.0.1/8',
                'LastReport': None,
                'UpdateStrategy': 'Disable',
                'LastChange': None,
                'MAC': '00:00:00:00:00:00',
                'UpToDate': None,
                'FQDN': None,
                'DiskProfile': 'S',
                'LastState': MachineStates.discovery,
                'Roles': ScheduleRoles.kubernetes_control_plane}
        )
        ui = user_interface.UserInterfaceRepository(sess_maker=self.sess_maker)
        data = ui.get_machines_overview()
        self.assertCountEqual(expect, data)

    def test_one_machine_full_scheduled_with_strategy(self):
        mac = "00:00:00:00:00:00"

        with session_commit(sess_maker=self.sess_maker) as session:
            uuid = "b7f5f93a-b029-475f-b3a4-479ba198cb8a"
            machine = Machine(uuid=uuid)
            session.add(machine)
            machine_id = session.query(Machine).filter(Machine.uuid == uuid).first().id
            session.add(
                MachineInterface(machine_id=machine_id, mac=mac, netmask=1, ipv4="10.10.10.10", cidrv4="127.0.0.1/8",
                                 as_boot=True, gateway="1.1.1.1", name="lol"))
            session.add(
                MachineDisk(path="/dev/sda", size=1024 * 1024 * 1024, machine_id=machine_id)
            )
            session.add(
                MachineCurrentState(machine_id=machine_id, machine_mac=mac, state_name=MachineStates.discovery)
            )
            session.add(
                Schedule(machine_id=machine_id, role=ScheduleRoles.kubernetes_control_plane)
            )
            session.add(
                LifecycleRolling(machine_id=machine_id, strategy="kexec", enable=True)
            )
            session.commit()

        expect = list()
        expect.append(
            {
                'CIDR': '127.0.0.1/8',
                'LastReport': None,
                'UpdateStrategy': 'kexec',
                'LastChange': None,
                'MAC': '00:00:00:00:00:00',
                'UpToDate': None,
                'FQDN': None,
                'DiskProfile': 'S',
                'LastState': MachineStates.discovery,
                'Roles': ScheduleRoles.kubernetes_control_plane}
        )
        ui = user_interface.UserInterfaceRepository(sess_maker=self.sess_maker)
        data = ui.get_machines_overview()
        self.assertCountEqual(expect, data)

    def test_one_machine_full_scheduled_with_strategy_disable(self):
        mac = "00:00:00:00:00:00"

        with session_commit(sess_maker=self.sess_maker) as session:
            uuid = "b7f5f93a-b029-475f-b3a4-479ba198cb8a"
            machine = Machine(uuid=uuid)
            session.add(machine)
            machine_id = session.query(Machine).filter(Machine.uuid == uuid).first().id
            session.add(
                MachineInterface(machine_id=machine_id, mac=mac, netmask=1, ipv4="10.10.10.10", cidrv4="127.0.0.1/8",
                                 as_boot=True, gateway="1.1.1.1", name="lol"))
            session.add(
                MachineDisk(path="/dev/sda", size=1024 * 1024 * 1024, machine_id=machine_id)
            )
            session.add(
                MachineCurrentState(machine_id=machine_id, machine_mac=mac, state_name=MachineStates.discovery)
            )
            session.add(
                Schedule(machine_id=machine_id, role=ScheduleRoles.kubernetes_control_plane)
            )
            session.add(
                LifecycleRolling(machine_id=machine_id, strategy="kexec", enable=False)
            )
            session.commit()

        expect = list()
        expect.append(
            {
                'CIDR': '127.0.0.1/8',
                'LastReport': None,
                'UpdateStrategy': 'Disable',
                'LastChange': None,
                'MAC': '00:00:00:00:00:00',
                'UpToDate': None,
                'FQDN': None,
                'DiskProfile': 'S',
                'LastState': MachineStates.discovery,
                'Roles': ScheduleRoles.kubernetes_control_plane}
        )
        ui = user_interface.UserInterfaceRepository(sess_maker=self.sess_maker)
        data = ui.get_machines_overview()
        self.assertCountEqual(expect, data)
