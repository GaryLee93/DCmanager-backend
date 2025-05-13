class SimpleDataCenter:
    def __init__(self, 
                id: str, 
                name: str, 
                height: int,
                n_rooms: int,
                n_racks: int,
                n_hosts: int
                ):
        self.id = id
        self.name = name
        self.height = height
        self.n_rooms = n_rooms
        self.n_racks = n_racks
        self.n_hosts = n_hosts

class SimpleRoom:
    def __init__(self,
                 id: str,
                 name: str,
                 height: int,
                 n_racks: int,
                 n_hosts: int,
                 dc_id: str):
        self.id = id
        self.name = name
        self.height = height
        self.n_racks = n_racks
        self.n_hosts = n_hosts
        self.dc_id = dc_id
    def toDICT(self):
        return {
			"id": self.id,
			"name": self.name,
			"height": self.height,
			"n_racks": self.n_racks,
            "n_hosts": self.n_hosts,
            "dc_id": self.dc_id  
		}


class SimpleRack:
    def __init__(self,
                id: str, 
                name: str, 
                height: int,
                capacity: int,
                n_hosts: int,
                service_id: str,
                room_id: str
                ):
        self.id = id
        self.name = name
        self.height = height
        self.capacity = capacity
        self.n_hosts = n_hosts
        self.service_id = service_id
        self.room_id = room_id

    def toDICT(self):
        return {
            "id": self.id,
            "name": self.name,
            "height": self.height,
            "capacity": self.capacity,
            "n_hosts": self.n_hosts,
            "service_id": self.service_id,
            "room_id": self.room_id
        }
    
class SimpleHost:
    def __init__(self, id: str, 
                name: str, 
                height: int,
                status: str,
                rack_id: str,
                pos: int
                ):
        self.id = id
        self.name = name
        self.height = height
        self.status = status
        self.rack_id = rack_id
        self.pos = pos

    def toDICT(self):
        return {
			"id": self.id,
			"name": self.name,
			"height": self.height,
			"status": self.status,
			"rack_id": self.rack_id,
			"pos": self.pos
		}

class SimpleService:
    def __init__(self,
                id: str,
                name: str,
                n_racks: int,
                n_hosts: int,
                total_ip = int):
        self.id = id
        self.name = name
        self.n_racks = n_racks
        self.n_hosts = n_hosts
        self.total_ip = total_ip    