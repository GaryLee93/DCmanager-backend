
#!/usr/bin/env python3
"""
DCManager 資料庫基礎 CRUD 測試腳本
此腳本會測試所有管理器的基本 CRUD 功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DataBaseManage import (
    test_connection,
    UserManager,
    DatacenterManager,
    RoomManager,
    RackManager,
    HostManager, 
    ServiceManager
)
from dataclasses import asdict
from pprint import pprint
import psycopg2
from DataBaseManage.connection import DB_CONFIG
def test_user_crud():
    """測試使用者 CRUD 操作"""
    print("\n=== 測試使用者管理 ===")
    
    user_manager = UserManager()
    
    # 創建使用者
    print("建立使用者...")
    admin = user_manager.createUser("admin_test1", "admin123", "manager")
    print(f"已建立管理員: {admin.username}, 角色: {admin.role}")
    
    operator = user_manager.createUser("operator_test", "op123", "normal")
    print(f"已建立操作員: {operator.username}, 角色: {operator.role}")
    
    # 讀取使用者
    print("\n查詢使用者...")
    admin_fetched = user_manager.getUser(username="admin_test1")
    print(f"查詢管理員: {admin_fetched.username}, 角色: {admin_fetched.role}")
    
    all_users = user_manager.getUser()
    print(f"總使用者數: {len(all_users)}")
    
    # 更新使用者
    print("\n更新使用者...")
    updated_admin = user_manager.updateUser("admin_test1", password="newpass123")
    print(f"更新管理員密碼完成: {updated_admin.username}")
    
    # 認證使用者
    print("\n認證使用者...")
    auth_result = user_manager.authenticate("admin_test1", "newpass123")
    print(f"認證結果: {'成功' if auth_result else '失敗'}")
    
    # 刪除使用者
    print("\n刪除使用者...")
    delete_result = user_manager.deleteUser("operator_test")
    print(f"刪除操作員結果: {'成功' if delete_result else '失敗'}")
    
    # 清理測試資料
    user_manager.deleteUser("admin_test1")
    
    return True

def test_datacenter_crud():
    """測試資料中心 CRUD 操作"""
    print("\n=== 測試資料中心管理 ===")
    
    dc_manager = DatacenterManager()
    
    # 創建資料中心
    print("建立資料中心...")
    dc1 = dc_manager.createDatacenter("TestDataCenter", 50)
    print(f"已建立資料中心: {dc1.name}, 預設高度: {dc1.height}")
    
    # 讀取資料中心
    dc1 = dc_manager.getDatacenter("TestDataCenter")
    print("\n查詢資料中心...")
    dc_fetched = dc_manager.getDatacenter("TestDataCenter")
    print(f"查詢資料中心: {dc_fetched.name}, 預設高度: {dc_fetched.height}")
    
    # 更新資料中心
    print("\n更新資料中心...")
    update_result = dc_manager.updateDatacenter("TestDataCenter", default_height=60)
    print(f"更新資料中心結果: {'成功' if update_result else '失敗'}")
    
    # 再次讀取資料中心確認更新
    dc_updated = dc_manager.getDatacenter("TestDataCenter")
    print(f"更新後資料中心: {dc_updated.name}, 預設高度: {dc_updated.height}")
    
    # 查詢所有資料中心
    all_dcs = dc_manager.getAllDatacenters()
    print(f"\n資料中心總數: {len(all_dcs)}")
    
    return dc1.name

def test_room_crud(dc_name):
    """測試機房 CRUD 操作"""
    print("\n=== 測試機房管理 ===")
    
    room_manager = RoomManager()
    
    # 創建機房
    print("建立機房...")
    room = room_manager.createRoom("Testroom", 30, dc_name)
    room_name = room.name
    print(f"已建立機房: {room_name}")
    # room_name = "TestRoom"
    # 讀取機房
    print("\n查詢機房...")
    try:
        room = room_manager.getRoom(room_name)
        print(f"查詢機房: {room.name}, 高度: {room.height}, 所屬資料中心: {room.dc_name}")
    except Exception as e:
        print(f"查詢機房時發生錯誤: {str(e)}")
        return room_name  # 仍然返回名稱以便清理
    
    # 更新機房
    print("\n更新機房...")
    update_result = room_manager.updateRoom(room_name, height=40)
    print(f"更新機房結果: {'成功' if update_result else '失敗'}")
    
    # 再次讀取機房確認更新
    room_updated = room_manager.getRoom(room_name)
    print(f"更新後機房: {room_updated.name}, 高度: {room_updated.height}")
    
    return room_name

def test_rack_crud(room_name):
    """測試機架 CRUD 操作"""
    print("\n=== 測試機架管理 ===")
    
    rack_manager = RackManager()
    
    # 創建機架
    print("建立機架...")
    rack = rack_manager.createRack("TestRack", 42, room_name)
    rack_name = rack.name
    print(f"已建立機架: {rack_name}")
    
    # 讀取機架
    print("\n查詢機架...")
    rack = rack_manager.getRack(rack_name)
    print(f"查詢機架: {rack.name}, 高度: {rack.height}, 所屬機房: {rack.room_name}")
    
    # 更新機架
    print("\n更新機架...")
    update_result = rack_manager.updateRack(rack_name, height=48)
    print(f"更新機架結果: {'成功' if update_result else '失敗'}")
    
    # 再次讀取機架確認更新
    try:
        rack_updated = rack_manager.getRack(rack_name)
        print(f"更新後機架: {rack_updated.name}, 高度: {rack_updated.height}")
    except Exception as e:
        print(f"注意: 在讀取更新後的機架時有例外 - {str(e)}")
    
    return rack_name

def test_service_crud(dc_name, username="admin_test1"):
    """測試服務 CRUD 操作"""
    print("\n=== 測試服務管理 ===")
    
    # 先建立一個使用者
    user_manager = UserManager()
    user_manager.createUser(username, "password123", "manager")
    
    service_manager = ServiceManager()
    
    # 創建服務
    print("建立服務...")
    n_allocated_racks = {dc_name: 0}  # 不分配機架
    allocated_subnets = ["192.168.1.0/28"]  # 分配一個子網
    
    service = service_manager.createService(
        "TestService", 
        n_allocated_racks, 
        allocated_subnets, 
        username
    )
    print(f"已建立服務: {service.name}")
    
    # 讀取服務
    print("\n查詢服務...")
    service_fetched = service_manager.getService("TestService")
    print(f"查詢服務: {service_fetched.name}")
    print(f"服務子網: {service_fetched.allocated_subnets}")
    print(f"可用IP數量: {len(service_fetched.available_ip_list)}")
    
    # 更新服務
    print("\n更新服務...")
    updated_service = service_manager.updateService(
        "TestService", 
        new_name="TestServiceUpdated",
        new_n_allocated_racks={dc_name: 0}
    )
    print(f"更新服務結果: {'成功' if updated_service else '失敗'}")
    
    # 讀取更新後的服務
    service_updated = service_manager.getService("TestServiceUpdated")
    print(f"更新後服務名稱: {service_updated.name}")
    
    # 擴展子網
    print("\n擴展服務子網...")
    extended_service = service_manager.extendsubnet(
        "TestServiceUpdated", 
        "192.168.2.0/28"
    )
    print(f"擴展後可用IP數量: {len(extended_service.available_ip_list)}")
    
    # 查詢所有服務
    all_services = service_manager.getAllServices()
    print(f"\n服務總數: {len(all_services)}")
    
    return service_updated.name

def test_host_crud(rack_name):
    """測試主機 CRUD 操作"""
    print("\n=== 測試主機管理 ===")
    
    host_manager = HostManager()
    
    # 創建主機
    print("建立主機...")
    host = host_manager.createHost("TestHost", 2, rack_name, 1)
    host_name = host.name
    print(f"已建立主機: {host_name}")
    
    # 讀取主機
    print("\n查詢主機...")
    host = host_manager.getHost(host_name)
    print(f"查詢主機: {host.name}, 高度: {host.height}, 所屬機架: {host.rack_name}, 位置: {host.pos}")
    
    # 更新主機
    print("\n更新主機...")
    update_result = host_manager.updateHost(host_name, new_running=False)
    print(f"更新主機結果: {'成功' if update_result else '失敗'}")
    
    # 再次讀取主機確認更新
    host_updated = host_manager.getHost(host_name)
    print(f"更新後主機: {host_updated.name}, 運行狀態: {host_updated.running}")
    
    # 查詢所有主機
    all_hosts = host_manager.getAllHosts()
    print(f"\n主機總數: {len(all_hosts) if all_hosts else 0}")
    
    return host_name

def test_service_assignment(service_name, rack_name):
    """測試機架指派給服務"""
    print("\n=== 測試機架指派 ===")
    
    service_manager = ServiceManager()
    
    # 指派機架到服務
    print("指派機架到服務...")
    assign_result = service_manager.assignRackToService(service_name, rack_name)
    print(f"指派結果: {'成功' if assign_result else '失敗'}")
    
    # 取消指派
    print("\n取消機架指派...")
    unassign_result = service_manager.unassignRackFromService(rack_name)
    print(f"取消指派結果: {'成功' if unassign_result else '失敗'}")
    
    return True
def cleanup(host_name, rack_name, room_name, service_name, dc_name, username="admin_test1"):
    """清理測試資料"""
    print("\n=== 清理測試資料 ===")
    
    host_manager = HostManager()
    rack_manager = RackManager()
    room_manager = RoomManager()
    service_manager = ServiceManager()
    dc_manager = DatacenterManager()
    user_manager = UserManager()
    
    # 刪除主機
    if host_name:
        try:
            result = host_manager.deleteHost(host_name)
            print(f"刪除主機結果: {'成功' if result else '失敗'}")
        except Exception as e:
            print(f"刪除主機異常: {str(e)}")
    
    # 刪除機架關聯
    if rack_name:
        try:
            # 先取消機架與服務的關聯
            conn = psycopg2.connect(**DB_CONFIG)
            with conn.cursor() as cursor:
                cursor.execute("UPDATE racks SET service_name = NULL WHERE name = %s", (rack_name,))
                conn.commit()
            conn.close()
            print(f"取消機架服務關聯成功")
            
            # 然後刪除機架
            result = rack_manager.deleteRack(rack_name)
            print(f"刪除機架結果: {'成功' if result else '失敗'}")
        except Exception as e:
            print(f"刪除機架異常: {str(e)}")
    
    # 刪除機房
    if room_name:
        try:
            result = room_manager.deleteRoom(room_name)
            print(f"刪除機房結果: {'成功' if result else '失敗'}")
        except Exception as e:
            print(f"刪除機房異常: {str(e)}")
    
    # 刪除所有 IP 和子網記錄
    if service_name:
        try:
            # 刪除 IP 記錄
            conn = psycopg2.connect(**DB_CONFIG)
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM IPs WHERE service_name = %s", (service_name,))
                cursor.execute("DELETE FROM subnets WHERE service_name = %s", (service_name,))
                conn.commit()
            conn.close()
            print(f"刪除 IP 和子網成功")
            
            # 刪除服務
            result = service_manager.deleteService(service_name)
            print(f"刪除服務結果: {'成功' if result else '失敗'}")
        except Exception as e:
            print(f"刪除服務異常: {str(e)}")
    
    # 檢查用戶是否仍有服務
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM services WHERE username = %s", (username,))
            service_count = cursor.fetchone()[0]
            if service_count > 0:
                print(f"警告: 用戶 {username} 仍有 {service_count} 個服務")
                # 刪除這些服務
                cursor.execute("SELECT name FROM services WHERE username = %s", (username,))
                services = cursor.fetchall()
                for service_record in services:
                    service_to_delete = service_record[0]
                    cursor.execute("DELETE FROM IPs WHERE service_name = %s", (service_to_delete,))
                    cursor.execute("DELETE FROM subnets WHERE service_name = %s", (service_to_delete,))
                    cursor.execute("UPDATE racks SET service_name = NULL WHERE service_name = %s", (service_to_delete,))
                    cursor.execute("DELETE FROM services WHERE name = %s", (service_to_delete,))
                    print(f"已刪除服務: {service_to_delete}")
                conn.commit()
        conn.close()
    except Exception as e:
        print(f"清理用戶服務異常: {str(e)}")
    
    # 刪除資料中心
    if dc_name:
        try:
            result = dc_manager.deleteDatacenter(dc_name)
            print(f"刪除資料中心結果: {'成功' if result else '失敗'}")
        except Exception as e:
            print(f"刪除資料中心異常: {str(e)}")
    
    # 刪除使用者
    try:
        result = user_manager.deleteUser(username)
        print(f"刪除使用者結果: {'成功' if result else '失敗'}")
    except Exception as e:
        print(f"刪除使用者異常: {str(e)}")
def run_all_tests():
    """執行所有測試"""
    print("開始執行 DCManager 資料庫 CRUD 測試")
    
    # 測試資料庫連線
    print("\n測試資料庫連線...")
    connection_ok = test_connection()
    print(f"資料庫連線測試結果: {'成功' if connection_ok else '失敗'}")
    
    if not connection_ok:
        print("資料庫連線失敗，測試中止")
        return
    
    # 測試使用者管理
    test_user_crud()
    
    # 測試資料中心管理
    dc_name = test_datacenter_crud()
    
    # 測試機房管理
    room_name = test_room_crud(dc_name) if dc_name else None
    
    # 測試機架管理
    rack_name = test_rack_crud(room_name) if room_name else None
    
    # 測試服務管理
    service_name = test_service_crud(dc_name) if dc_name else None
    
    # 測試主機管理
    host_name = test_host_crud(rack_name) if rack_name else None
    
    # 測試服務與機架之間的關係
    if service_name and rack_name:
        test_service_assignment(service_name, rack_name)
    
    # 清理測試資料
    cleanup(host_name, rack_name, room_name, service_name, dc_name)
    
    print("\n所有測試完成!")

if __name__ == "__main__":
    try:
        run_all_tests()
    except Exception as e:
        print(f"\n測試中發生未捕獲的異常: {str(e)}")