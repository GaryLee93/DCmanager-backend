from DataBaseManage import (
    IPRangeManager,
    DatacenterManager,
    RoomManager,
    RackManager,
    HostManager,
    ServiceManager,
    UserManager,
)


def test_crud_operations():

    print("Testing CRUD Operations for Datacenter Management System")

    # ----- Test UserManager CRUD -----
    # print("\n=== Testing UserManager CRUD ===")
    # user_manager = UserManager()

    # # Create
    # print("Creating a test user...")
    # test_user = user_manager.createUser("testuser", "password123", "normal")
    # print(f"Created user: {test_user.username} with ID: {test_user.id}")

    # # Read
    # print("Reading the user...")
    # retrieved_user = user_manager.getUser(test_user.id)
    # print(f"Retrieved user: {retrieved_user.username}, Role: {retrieved_user.role}")

    # # Update
    # print("Updating the user...")
    # updated_user = user_manager.updateUser(test_user.id, role="manager")
    # print(f"Updated user: {updated_user.username}, New role: {updated_user.role}")

    # ----- Test DatacenterManager CRUD -----
    print("\n=== Testing DatacenterManager CRUD ===")
    datacenter_manager = DatacenterManager()

    # Create
    print("Creating a test datacenter...")
    test_dc = datacenter_manager.createDatacenter("Test Datacenter", 42)
    print(f"Created datacenter: {test_dc.name} with ID: {test_dc.id}")

    # Read
    print("Reading the datacenter...")
    retrieved_dc = datacenter_manager.getDatacenter(test_dc.id)
    print(f"Retrieved datacenter: {retrieved_dc.name}, Height: {retrieved_dc.height}")

    # Update
    print("Updating the datacenter...")
    updated_dc = datacenter_manager.updateDatacenter(
        test_dc.id, name="Updated Datacenter"
    )
    print(f"Updated datacenter: {updated_dc.name}")

    # ----- Test Service and Room Managers -----
    print("\n=== Testing ServiceManager and RoomManager CRUD ===")
    service_manager = ServiceManager()
    room_manager = RoomManager()

    # Create service
    test_service = service_manager.createService(
        "Test Service", racks=None, ip_list=["192.168.1.40"]
    )
    print(f"Created service: {test_service.name} with ID: {test_service.id}")
    print(f"Service IP list: {test_service.ip_list}")
    # Create room
    room_id = room_manager.createRoom("Test Room", 40, test_dc.id)
    print(f"Created room with ID: {room_id}")

    # ----- Test RackManager CRUD -----
    print("\n=== Testing RackManager CRUD ===")
    rack_manager = RackManager()

    # Create rack
    rack_id = rack_manager.createRack("Test Rack", 38, room_id, test_service.id)
    print(f"Created rack with ID: {rack_id}")
    # create IP range
    ip_range_manager = IPRangeManager()
    ip_range = ip_range_manager.add_ip_range(test_dc.id, "192.168.1.30", "192.168.1.45")
    print(f"Created IP range: {ip_range.start_IP} - {ip_range.end_IP}")
    # ----- Test HostManager CRUD -----
    print("\n=== Testing HostManager CRUD ===")
    host_manager = HostManager()

    # Create host
    # IP = "192.168.1.40"  # ✅ Valid format (from your IP range)
    # host_id = host_manager.createHost("Test Host", 1, IP, rack_id, test_service.id, pos=1)
    # print(f"Created host with ID: {host_id}")

    # ----- Test IPRangeManager CRUD -----
    print("\n=== Testing IPRangeManager CRUD ===")
    ip_range_manager = IPRangeManager()

    # Create IP range
    test_ip_range = ip_range_manager.add_ip_range(test_dc.id, "10.0.0.1", "10.0.0.254")
    print(f"Created IP range: {test_ip_range.start_IP} - {test_ip_range.end_IP}")

    # ----- Clean Up in Reverse Order -----
    print("\n=== Cleaning Up ===")

    # # Delete Host
    # print("Deleting host...")
    # success = host_manager.deleteHost(host_id)
    # print(f"Host deleted: {success}")

    # Delete Rack
    print("Deleting rack...")
    success = rack_manager.deleteRack(rack_id)
    print(f"Rack deleted: {success}")

    # Delete Room
    print("Deleting room...")
    success = room_manager.deleteRoom(room_id)
    print(f"Room deleted: {success}")

    # Delete Service
    print("Deleting service...")
    success = service_manager.deleteService(test_service.id)
    print(f"Service deleted: {success}")

    # Delete Datacenter
    print("Deleting datacenter...")
    success = datacenter_manager.deleteDatacenter(test_dc.id)
    print(f"Datacenter deleted: {success}")

    # Delete User
    print("Deleting user...")
    user_manager = UserManager()
    test_user = user_manager.getUser(username="testuser")
    success = user_manager.deleteUser(test_user.id)
    print(f"User deleted: {success}")

    print("\nAll CRUD tests completed!")


if __name__ == "__main__":
    test_crud_operations()
