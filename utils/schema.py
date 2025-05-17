from utils.simpleSchema import SimpleDataCenter, SimpleRoom, SimpleRack, SimpleHost, SimpleService

class IP_range:
    def __init__(self, start_IP: str, end_IP: str):
        self.start_IP = start_IP
        self.end_IP = end_IP

class DataCenter:
    def __init__(self, 
                 id: str, 
                 name: str, 
                 height: int,
                 n_rooms: int,
                 rooms: list[SimpleRoom],
                 n_racks: int,
                 n_hosts: int,
                 ip_ranges: list[IP_range]
                ):
        self.id = id
        self.name = name
        self.height = height
        self.n_rooms = n_rooms
        self.rooms = rooms
        self.n_racks = n_racks
        self.n_hosts = n_hosts
        self.ip_ranges = ip_ranges

    def toDICT(self):
        return {
            "id": self.id,
            "name": self.name,
            "height": self.height,
            "n_rooms": self.n_rooms,
            "rooms": [room.toDICT() for room in self.rooms],
            "n_racks": self.n_racks,
            "n_hosts": self.n_hosts,
            "ip_ranges": [ip_range.__dict__ for ip_range in self.ip_ranges]
        } 

class Room:
    def __init__(self, 
                 id: str, 
                 name: str, 
                 height: int,
                 n_racks: int,
                 racks: list[SimpleRack],
                 n_hosts: int,
                 dc_id: str
                ):
        self.id = id
        self.name = name
        self.height = height
        self.n_racks = n_racks
        self.racks = racks
        self.n_hosts = n_hosts
        self.dc_id = dc_id

    def toDICT(self):
        return {
            "id": self.id,
            "name": self.name,
            "height": self.height,
            "racks": [rack.toDICT() for rack in self.racks],
            "n_racks": self.n_racks,
            "n_hosts": self.n_hosts,
            "dc_id": self.dc_id
        }

class Rack:
    def __init__(self, 
                 id: str, 
                 name: str, 
                 height: int, 
                 capacity: int,
                 n_hosts: int,
                 hosts: list[SimpleHost],
                 service_id: str,
                 dc_id: str,
                 room_id: str
                ):
        self.id = id
        self.name = name
        self.height = height
        self.capacity = capacity
        self.n_hosts = n_hosts
        self.hosts = hosts
        self.service_id = service_id
        self.dc_id = dc_id
        self.room_id = room_id

    def toDICT(self):
        return {
            "id": self.id,
            "name": self.name,
            "height": self.height,
            "capacity": self.capacity,
            "n_hosts": self.n_hosts,
            "hosts": [host.toDICT() for host in self.hosts],
            "service_id": self.service_id,
            "dc_id": self.dc_id,
            "room_id": self.room_id
        }

class Host:
    def __init__(self, 
                 id: str, 
                 name: str,
                 height: int,
                 ip: str, 
                 status: str,
                 service_id: str,
                 dc_id: str,
                 room_id: str,
                 rack_id: str,
                 pos: int
                ):
        self.id = id
        self.name = name
        self.height = height
        self.ip = ip
        self.status = status
        self.service_id = service_id
        self.dc_id = dc_id
        self.room_id = room_id
        self.rack_id = rack_id
        self.pos = pos
    
    def toDICT(self):
        return {
            "id": self.id,
            "name": self.name,
            "height": self.height,
            "ip": self.ip,
            "status": self.status,
            "service_id": self.service_id,
            "dc_id": self.dc_id,
            "room_id": self.room_id,
            "rack_id": self.rack_id,
            "pos": self.pos
        }

class Service:
    def __init__(self, 
                 id: str, 
                 name: str,
                 n_racks: int,
                 racks: list[SimpleRack],
                 n_hosts: int,
                 total_ip: int,
                 ip_list: list[str]
                ):
        self.id = id
        self.name = name
        self.racks = racks
        self.n_racks = n_racks
        self.n_hosts = n_hosts
        self.total_ip = total_ip
        self.ip_list = ip_list

class User:
    def __init__(self,
                 id: str, 
                 username: str,  
                 password: str, 
                 role: str
                ):
        self.id = id
        self.username = username
        self.password = password
        self.role = role