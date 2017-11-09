from enjoliver.repositories.machine_discovery_repo import DiscoveryRepository
from enjoliver.repositories.machine_schedule_repo import ScheduleRepository
from enjoliver.repositories.machine_state_repo import MachineStateRepository
from enjoliver.repositories.user_interface_repo import UserInterfaceRepository
from enjoliver.smartdb import SmartDatabaseClient


class RepositoriesRegister:
    def __init__(self, smart: SmartDatabaseClient):
        self.discovery = DiscoveryRepository(smart)
        self.machine_state = MachineStateRepository(smart)
        self.user_interface = UserInterfaceRepository(smart)
        self.machine_schedule = ScheduleRepository(smart)
