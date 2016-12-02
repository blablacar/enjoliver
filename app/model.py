import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Machine(Base):
    __tablename__ = 'machine'
    uuid = Column(String, primary_key=True, autoincrement=False, nullable=False)

    interfaces = relationship("MachineInterface", lazy="joined")
    created_date = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return "<%s: %s>" % (Machine.__name__, self.uuid)


class MachineInterface(Base):
    __tablename__ = 'machine-interface'

    mac = Column(String, nullable=False, primary_key=True, autoincrement=False)
    name = Column(String, nullable=False)
    netmask = Column(Integer, nullable=False)
    ipv4 = Column(String, nullable=False)
    cidrv4 = Column(String, nullable=False)
    as_boot = Column(Boolean, default=False)

    machine_uuid = Column(Integer, ForeignKey('machine.uuid'))
    chassis_port = relationship("ChassisPort")

    def __repr__(self):
        return "<%s: %s %s>" % (MachineInterface.__name__, self.mac, self.cidrv4)


class Chassis(Base):
    __tablename__ = 'chassis'

    name = Column(String, nullable=False)
    mac = Column(String, nullable=False, primary_key=True)

    ports = relationship("ChassisPort", lazy="joined")

    def __repr__(self):
        return "<%s: mac:%s name:%s>" % (Chassis.__name__, self.mac, self.name)


class ChassisPort(Base):
    __tablename__ = 'chassis-port'

    mac = Column(String, primary_key=True, autoincrement=False)
    chassis_mac = Column(String, ForeignKey('chassis.mac'))

    machine_interface_mac = Column(String, ForeignKey('machine-interface.mac'))

    def __repr__(self):
        return "<%s: mac:%s chassis_mac:%s>" % (ChassisPort.__name__, self.mac, self.chassis_mac)
