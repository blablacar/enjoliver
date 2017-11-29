import logging

from sqlalchemy.orm import joinedload, sessionmaker

from enjoliver.db import session_commit
from enjoliver.model import Machine, Schedule, MachineInterface

logger = logging.getLogger(__name__)


class MachineScheduleRepository:
    __name__ = "MachineScheduleRepository"

    def __init__(self, sess_maker: sessionmaker):
        self.__sess_maker = sess_maker

    @staticmethod
    def _lint_schedule_data(schedule_data: dict):
        try:
            assert 'selector' in schedule_data
            assert 'mac' in schedule_data['selector']
            assert 'roles' in schedule_data
        except AssertionError as e:
            err_msg = "missing keys in schedule data: '%s'" % e
            logger.error(err_msg)
            raise TypeError(err_msg)

        return schedule_data

    def create_schedule(self, schedule_data: dict):
        schedule_data = self._lint_schedule_data(schedule_data)

        with session_commit(sess_maker=self.__sess_maker) as session:
            machine = session.query(Machine) \
                .join(MachineInterface) \
                .options(joinedload("schedules")) \
                .filter(MachineInterface.mac == schedule_data["selector"]["mac"]) \
                .first()

            if not machine:
                logger.error("machine mac %s not in db", schedule_data["selector"]["mac"])
            else:
                machine_already_scheduled = [s.role for s in machine.schedules]
                for role in schedule_data["roles"]:
                    if role in machine_already_scheduled:
                        logger.info("machine mac %s already scheduled with role %s",
                                    schedule_data["selector"]["mac"], role)
                        continue
                    session.add(Schedule(machine_id=machine.id, role=role))
                    logger.info(
                        "scheduling machine mac %s as role %s",
                        schedule_data["selector"]["mac"], role
                    )

    def get_all_schedules(self):
        result = dict()
        with session_commit(sess_maker=self.__sess_maker) as session:
            for machine in session.query(Machine) \
                    .options(joinedload("interfaces")) \
                    .options(joinedload("schedules")) \
                    .join(Schedule) \
                    .filter(MachineInterface.as_boot == True):
                if machine.schedules:
                    result[machine.interfaces[0].mac] = [k.role for k in machine.schedules]

        return result

    def get_roles_by_mac_selector(self, mac: str):
        with session_commit(sess_maker=self.__sess_maker) as session:
            return [
                s.role for s in session.query(Schedule)
                .join(Machine)
                .join(MachineInterface)
                .filter(MachineInterface.mac == mac)
            ]

    def get_available_machines(self):
        available_machines = []
        with session_commit(sess_maker=self.__sess_maker) as session:
            for m in session.query(Machine) \
                    .join(MachineInterface) \
                    .options(joinedload("schedules")) \
                    .options(joinedload("interfaces")) \
                    .options(joinedload("disks")) \
                    .filter(MachineInterface.as_boot == True):
                # TODO find a way to support cockroach and SQLite without this if
                if not m.schedules:
                    available_machines.append({
                        "mac": m.interfaces[0].mac,
                        "ipv4": m.interfaces[0].ipv4,
                        "cidrv4": m.interfaces[0].cidrv4,
                        "as_boot": m.interfaces[0].as_boot,
                        "name": m.interfaces[0].name,
                        "fqdn": m.interfaces[0].fqdn,
                        "netmask": m.interfaces[0].netmask,
                        "created_date": m.created_date,
                        "disks": [{"path": k.path, "size-bytes": k.size} for k in m.disks],
                    })

        return available_machines

    def _construct_machine_dict(self, machine: Machine, role):
        return {
            "mac": machine.interfaces[0].mac,
            "ipv4": machine.interfaces[0].ipv4,
            "cidrv4": machine.interfaces[0].cidrv4,
            "gateway": machine.interfaces[0].gateway,
            "as_boot": machine.interfaces[0].as_boot,
            "name": machine.interfaces[0].name,
            "netmask": machine.interfaces[0].netmask,
            "roles": role,
            "created_date": machine.created_date,
            "fqdn": machine.interfaces[0].fqdn,
            "disks": [{"path": k.path, "size-bytes": k.size} for k in machine.disks],
        }

    def get_machines_by_role(self, role: str):
        machines = []
        with session_commit(sess_maker=self.__sess_maker) as session:
            for machine in session.query(Machine) \
                    .options(joinedload("interfaces")) \
                    .options(joinedload("disks")) \
                    .join(Schedule) \
                    .filter(MachineInterface.as_boot == True) \
                    .filter(Schedule.role == role):
                machines.append(self._construct_machine_dict(machine, role))

        return machines

    def get_machines_by_roles(self, *roles):
        if len(roles) == 1:
            return self.get_machines_by_role(roles[0])
        machines = []
        roles = list(roles)

        with session_commit(sess_maker=self.__sess_maker) as session:
            for machine in session.query(Machine) \
                    .options(joinedload("interfaces")) \
                    .options(joinedload("disks")) \
                    .join(Schedule) \
                    .filter(MachineInterface.as_boot == True):
                # TODO Maybe do this with a sqlalchemy filter func
                if len(roles) == len(roles) and set(k.role for k in machine.schedules) == set(roles):
                    machines.append(self._construct_machine_dict(machine, roles))

        return machines

    def get_role_ip_list(self, role: str):
        ips = []
        with session_commit(sess_maker=self.__sess_maker) as session:
            for machine in session.query(Machine) \
                    .options(joinedload("interfaces")) \
                    .join(MachineInterface) \
                    .join(Schedule) \
                    .filter(Schedule.role == role, MachineInterface.as_boot == True):
                ips.append(machine.interfaces[0].ipv4)

        return ips
