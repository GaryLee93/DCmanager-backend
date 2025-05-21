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
class SimpleRack:
    name: str
    height: int
    capacity: int  # 還剩多少容量
    n_hosts: int
    service_name: str
    room_name: str


@dataclass
class Room:
    name: str
    height: int
    n_racks: int
    racks: list[SimpleRack]
    n_hosts: int
    name: str
    height: int
    capacity: int  # 還剩多少容量
    n_hosts: int
    hosts: list[Host]
    service_name: str
    dc_name: str
    room_name: str
    dc_name: str


@dataclass
class SimpleRoom:
    name: str
    height: int
    n_racks: int
    n_hosts: int
    dc_name: str


@dataclass
class DataCenter:
    name: str
    height: int
    n_rooms: int
    rooms: list[SimpleRoom]
    n_racks: int
    n_hosts: int


@dataclass
class SimpleDataCenter:
    name: str
    height: int
    n_rooms: int
    n_racks: int
    n_hosts: int


@dataclass
class Service:
    name: str
    allocated_racks: dict[
        str, list[SimpleRack]
    ]  # how many racks are allocated in each dc
    hosts: list[Host]
    username: int
    allocated_subnet: str
    total_ip_list: list[str]
    available_ip_list: list[str]


@dataclass
class SimpleService:
    name: str
    n_allocated_racks: dict[str, int]  # how many racks are allocated in each dc
    n_hosts: int
    username: int
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
