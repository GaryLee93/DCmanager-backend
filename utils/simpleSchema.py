from dataclasses import dataclass


@dataclass
class SimpleDataCenter:
    id: str
    name: str
    height: int
    n_rooms: int
    n_racks: int
    n_hosts: int


@dataclass
class SimpleRoom:
    id: str
    name: str
    height: int
    n_racks: int
    n_hosts: int
    dc_id: str


@dataclass
class SimpleRack:
    id: str
    name: str
    height: int
    capacity: int  # 還剩多少容量
    n_hosts: int
    service_id: str
    service_name: str
    room_id: str


@dataclass
class SimpleHost:
    id: str
    name: str
    height: int
    ip: str
    running: bool
    rack_id: str
    pos: int  # 在rack的第幾個位置


@dataclass
class SimpleService:
    id: str
    name: str
    n_racks: int
    n_hosts: int
    total_ip: int
    available_ip: int
