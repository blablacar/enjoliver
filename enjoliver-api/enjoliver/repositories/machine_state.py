import datetime
import logging

from sqlalchemy.orm import joinedload, sessionmaker, Session

from enjoliver.db import session_commit
from enjoliver.model import MachineCurrentState, MachineInterface

logger = logging.getLogger(__name__)


class MachineStateRepository:
    def __init__(self, sess_maker: sessionmaker):
        self.__sess_maker = sess_maker

    def _update_state(self, session: Session, machine_current_state: MachineCurrentState):
        try:
            session.add(machine_current_state)
        except Exception as e:
            # updating state is not critical so we accept to wide catch all exception and pass over it just with a log
            logger.error("fail to update machine with mac: %s with state %s: %s" % (
                machine_current_state.machine_mac, machine_current_state.state_name, e))

    def fetch(self, finished_in_less_than_min: int):
        time_limit = datetime.datetime.utcnow() - datetime.timedelta(minutes=finished_in_less_than_min)
        results = []
        with session_commit(sess_maker=self.__sess_maker) as session:
            for machine in session.query(MachineCurrentState) \
                    .options(joinedload("interfaces")) \
                    .filter(MachineCurrentState.updated_date > time_limit) \
                    .order_by(MachineCurrentState.updated_date.desc()):
                results.append({
                    "fqdn": machine.interfaces[0].fqdn if machine.interfaces else None,
                    "mac": machine.interfaces[0].mac if machine.interfaces else machine.machine_mac,
                    "state": machine.state_name,
                    "date": machine.updated_date
                })
            return results

    def update(self, mac: str, state: str):
        with session_commit(sess_maker=self.__sess_maker) as session:
            state_machine = session.query(MachineCurrentState) \
                .filter(MachineCurrentState.machine_mac == mac) \
                .one_or_none()

            machine_interface = session.query(MachineInterface) \
                .filter(MachineInterface.mac == mac) \
                .one_or_none()

            now = datetime.datetime.utcnow()
            machine_id = None
            if machine_interface is not None:
                machine_id = machine_interface.machine_id

            if not state_machine:
                logger.debug(
                    "machine with mac: %s doesn't exist in table %s: creating with state %s" % (
                        mac, MachineCurrentState.__tablename__, state))
                self._update_state(session, MachineCurrentState(
                    machine_id=machine_id,
                    state_name=state,
                    machine_mac=mac,
                    created_date=now,
                    updated_date=now,
                ))
            else:
                state_machine.state_name = state
                state_machine.machine_id = machine_id
                state_machine.updated_date = now
                self._update_state(session, state_machine)
