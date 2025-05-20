from dataclasses import dataclass


@dataclass
class SimpleDataCenter:
    name: str
    height: int
    n_rooms: int
    n_racks: int
    n_hosts: int


@dataclass
class SimpleRoom:
    name: str
    height: int
    n_racks: int
    n_hosts: int
    dc_name: str


@dataclass
class SimpleRack:
    name: str
    height: int
    capacity: int  # 還剩多少容量
    n_hosts: int
    service_name: str
    room_name: str


@dataclass
class SimpleHost:
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
class SimpleService:
    name: str
    n_allocated_racks: int
    n_hosts: int
    allocated_subnet: str
    total_ip_list: list[str]
    available_ip_list: list[str]
