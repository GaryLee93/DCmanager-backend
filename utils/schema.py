from utils.simpleSchema import *
from dataclasses import dataclass
from enum import Enum


@dataclass
class Host:
    name: str
    height: int
    ip: str
    running: bool
    service_name: str
    dc_name: str
    room_name: str
    rack_name: str
    pos: int  # 在rack的第幾個位置


@dataclass
class DataCenter:
    name: str
    height: int
    n_rooms: int
    rooms: list[SimpleRoom]
    n_racks: int
    n_hosts: int


@dataclass
class Room:
    name: str
    height: int
    n_racks: int
    racks: list[SimpleRack]
    n_hosts: int
    dc_name: str


@dataclass
class Rack:
    name: str
    height: int
    capacity: int  # 還剩多少容量
    n_hosts: int
    hosts: list[Host]
    service_name: str
    dc_name: str
    room_name: str


@dataclass
class Service:
    name: str
    allocated_racks: list[SimpleRack]
    hosts: list[Host]
    allocated_subnet: str
    total_ip_list: list[str]
    available_ip_list: list[str]


class UserRole(Enum):
    NORMAL = "normal"
    MANAGER = "manager"


@dataclass
class User:
    id: str
    username: str
    password: str
    role: UserRole
