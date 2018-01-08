from enjoliver.repositories.machine_discovery import MachineDiscoveryRepository
from enjoliver.repositories.machine_schedule import MachineScheduleRepository
from enjoliver.repositories.machine_state import MachineStateRepository
from enjoliver.repositories.user_interface import UserInterfaceRepository

from sqlalchemy.orm import sessionmaker


class RepositoryRegistry:
    """
    A registry of usable repositories for the enjoliver API. It could be seen as a Service Registry.
    The only dependency is the DB session factory: sess_maker.
    """
    # TODO: add other dependencies here (config, cache, ...)
    def __init__(self, sess_maker: sessionmaker):
        self.discovery = MachineDiscoveryRepository(sess_maker)
        self.machine_state = MachineStateRepository(sess_maker)
        self.user_interface = UserInterfaceRepository(sess_maker)
        self.machine_schedule = MachineScheduleRepository(sess_maker)
