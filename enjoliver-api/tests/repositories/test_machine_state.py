import unittest

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from enjoliver.db import session_commit
from enjoliver.model import Base, Machine, MachineCurrentState, MachineInterface, MachineStates
from enjoliver.repositories.machine_state import MachineStateRepository


class TestMachineStateRepo(unittest.TestCase):
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

    def test_no_machine_no_state(self):
        mac = "00:00:00:00:00:00"
        state = MachineStates.booting
        msr = MachineStateRepository(sess_maker=self.sess_maker)
        msr.update(mac, state)

        with session_commit(sess_maker=self.sess_maker) as session:
            res = session.query(MachineCurrentState).filter(MachineCurrentState.machine_mac == mac).first()
            self.assertEqual(mac, res.machine_mac)
            self.assertEqual(state, res.state_name)
            self.assertEqual(None, res.machine_id)

    def test_machine_exists_no_state(self):
        mac = "00:00:00:00:00:00"
        state = MachineStates.booting

        with session_commit(sess_maker=self.sess_maker) as session:
            uuid = "b7f5f93a-b029-475f-b3a4-479ba198cb8a"
            machine = Machine(uuid=uuid)
            session.add(machine)
            machine_id = session.query(Machine).filter(Machine.uuid == uuid).first().id
            session.add(
                MachineInterface(machine_id=machine_id, mac=mac, netmask=1, ipv4="10.10.10.10", cidrv4="127.0.0.1/8",
                                 as_boot=True, gateway="1.1.1.1", name="lol"))
            session.commit()

        msr = MachineStateRepository(sess_maker=self.sess_maker)
        msr.update(mac, state)

        with session_commit(sess_maker=self.sess_maker) as session:
            res = session.query(MachineCurrentState).filter(MachineCurrentState.machine_mac == mac).first()
            self.assertEqual(mac, res.machine_mac)
            self.assertEqual(state, res.state_name)
            self.assertEqual(machine_id, res.machine_id)

    def test_machine_exists_state_exists(self):
        mac = "00:00:00:00:00:00"
        state = MachineStates.booting

        with session_commit(sess_maker=self.sess_maker) as session:
            uuid = "b7f5f93a-b029-475f-b3a4-479ba198cb8a"
            machine = Machine(uuid=uuid)
            session.add(machine)
            machine_id = session.query(Machine).filter(Machine.uuid == uuid).first().id
            session.add(
                MachineInterface(machine_id=machine_id, mac=mac, netmask=1, ipv4="10.10.10.10", cidrv4="127.0.0.1/8",
                                 as_boot=True, gateway="1.1.1.1", name="lol"))
            session.commit()

        msr = MachineStateRepository(sess_maker=self.sess_maker)
        msr.update(mac, state)

        new_state = MachineStates.discovery
        msr.update(mac, new_state)

        with session_commit(sess_maker=self.sess_maker) as session:
            res = session.query(MachineCurrentState).filter(MachineCurrentState.machine_mac == mac).first()
            self.assertEqual(mac, res.machine_mac)
            self.assertEqual(new_state, res.state_name)
            self.assertEqual(machine_id, res.machine_id)
            updated_date = res.updated_date

        ret = msr.fetch(10)
        self.assertEqual([{
            "fqdn": None,
            "mac": mac,
            "state": new_state,
            "date": updated_date
        }], ret)
