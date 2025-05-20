from utils.simpleSchema import *
from dataclasses import dataclass
from enum import Enum


@dataclass
class IP_Range:
    start_IP: str
    end_IP: str


@dataclass
class DataCenter:
    id: str
    name: str
    height: int
    n_rooms: int
    rooms: list[SimpleRoom]
    n_racks: int
    n_hosts: int
    ip_ranges: list[IP_Range]


@dataclass
class Room:
    id: str
    name: str
    height: int
    n_racks: int
    racks: list[SimpleRack]
    n_hosts: int
    dc_id: str
    dc_name: str


@dataclass
class Rack:
    id: str
    name: str
    height: int
    capacity: int  # 還剩多少容量
    n_hosts: int
    hosts: list[SimpleHost]
    service_id: str
    service_name: str
    dc_id: str
    dc_name: str
    room_id: str
    room_name: str


@dataclass
class Host:
    id: str
    name: str
    height: int
    ip: str
    running: bool
    service_id: str
    service_name: str
    dc_id: str
    dc_name: str
    room_id: str
    room_name: str
    rack_id: str
    rack_name: str
    pos: int  # 在rack的第幾個位置


@dataclass
class Service:
    id: str
    name: str
    n_racks: int
    racks: list[SimpleRack]
    n_hosts: int
    total_ip: int
    total_ip_list: list[str]
    available_ip: int
    available_ip_list: list[str]
    dc_id: str
    dc_name: str


class UserRole(Enum):
    NORMAL = "normal"
    MANAGER = "manager"


@dataclass
class User:
    id: str
    username: str
    password: str
    role: UserRole
