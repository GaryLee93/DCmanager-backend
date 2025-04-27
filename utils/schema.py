class DataCenter:
    def __init__(self, 
                 id: str, 
                 name: str, 
                 default_height: int,
                 rooms: list,
                 n_rooms: int,
                 n_racks: int,
                 n_hosts: int
                ):
        self.id = id
        self.name = name
        self.default_height = default_height
        self.rooms = rooms
        self.n_rooms = n_rooms
        self.n_racks = n_racks
        self.n_hosts = n_hosts

class Room:
    def __init__(self, 
                 id: str, 
                 name: str, 
                 height: int, 
                 racks: list,
                 n_racks: int,
                 n_hosts: int,
                 dc_id: str
                ):
        self.id = id
        self.name = name
        self.height = height
        self.racks = racks
        self.n_racks = n_racks
        self.n_hosts = n_hosts
        self.dc_id = dc_id

class Rack:
    def __init__(self, 
                 id: str, 
                 name: str, 
                 height: int, 
                 hosts: list,
                 n_hosts: int,
                 service_id: str,
                 dc_id: str,
                 room_id: str
                ):
        self.id = id
        self.name = name
        self.height = height
        self.hosts = hosts
        self.n_hosts = n_hosts
        self.service_id = service_id
        self.dc_id = dc_id
        self.room_id = room_id

class Host:
    def __init__(self, 
                 id: str, 
                 name: str,
                 height: int,
                 ip: str, 
                 service_id: str,
                 dc_id: str,
                 room_id: str,
                 rack_id: str
                ):
        self.id = id
        self.name = name
        self.height = height
        self.ip = ip
        self.service_id = service_id
        self.dc_id = dc_id
        self.room_id = room_id
        self.rack_id = rack_id

class IP_Subnet:
    def __init__(self, 
                 ip: str,
                 mask: int
                ):
        self.ip = ip
        self.mask = mask

class Service:
    def __init__(self, 
                 id: str, 
                 name: str, 
                 racks: str,
                 n_racks: int,
                 subnet: IP_Subnet
                ):
        self.id = id
        self.name = name
        self.racks = racks
        self.n_racks = n_racks
        self.subnet = subnet

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

class Company_IP_Subnets:
    def __init__(self, ip_subnets: list):
        self.ip_subnets = ip_subnets