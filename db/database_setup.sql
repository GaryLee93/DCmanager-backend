-- CREATE DATABASE datacenter_management;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

------------------------------------------------------------
-------------  Table Creation and Constraints --------------
------------------------------------------------------------
-- Table for users, with permissions
CREATE TABLE users (
    username VARCHAR(255) PRIMARY KEY, -- Unique username
    password VARCHAR(255) NOT NULL, -- Password (hashed)
    role VARCHAR(50) NOT NULL CHECK (role IN ('normal', 'admin')), -- User role (changed from permission to role)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for services
CREATE TABLE services (
    name VARCHAR(255) PRIMARY KEY, -- Name of the service
    username VARCHAR(255) NOT NULL REFERENCES users(username) ON UPDATE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- Table for datacenters, storing basic information and statistics
CREATE TABLE datacenters (
    name VARCHAR(255) PRIMARY KEY, -- Name of the datacenter
    height INTEGER NOT NULL, -- Height of the datacenter
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for rooms, linked to datacenters
CREATE TABLE rooms (
    name VARCHAR(255) PRIMARY KEY, -- Name of the room
    height INTEGER NOT NULL, -- Height of the room
    dc_name VARCHAR(255) NOT NULL REFERENCES datacenters(name) ON UPDATE CASCADE, -- Name of the datacenter (redundant for faster access)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for racks, linked to rooms, datacenters, and services
CREATE TABLE racks (
    name VARCHAR(255) PRIMARY KEY, -- Name of the rack
    height INTEGER NOT NULL, -- Height of the rack
    service_name VARCHAR(255) REFERENCES services(name) ON UPDATE CASCADE, -- Name of the service (redundant for faster access)
    dc_name VARCHAR(255) REFERENCES datacenters(name) ON UPDATE CASCADE, -- Name of the datacenter (redundant for faster access)
    room_name VARCHAR(255) REFERENCES rooms(name) ON UPDATE CASCADE, -- Name of the room (redundant for faster access)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for service IPs
CREATE TABLE IPs (
    ip INET PRIMARY KEY, -- IP address
    service_name VARCHAR(255) NOT NULL REFERENCES services(name) ON UPDATE CASCADE, -- Name of the service (redundant for faster access)
    assigned BOOLEAN DEFAULT FALSE, -- Whether this IP is assigned to a host
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for hosts, linked to racks, rooms, datacenters, and services
CREATE TABLE hosts (
    name VARCHAR(255) PRIMARY KEY, -- Name of the host
    height INTEGER NOT NULL,
    ip INET REFERENCES IPs(ip) ON UPDATE CASCADE, -- IP address (linked to service_ips)
    running BOOLEAN DEFAULT FALSE, -- Whether the host is running
    service_name VARCHAR(255), -- Name of the service (redundant for faster access)
    dc_name VARCHAR(255) REFERENCES datacenters(name) ON UPDATE CASCADE, -- Name of the datacenter (redundant for faster access)
    room_name VARCHAR(255) REFERENCES rooms(name) ON UPDATE CASCADE, -- Name of the room (redundant for faster access)
    rack_name VARCHAR(255)  REFERENCES racks(name) ON UPDATE CASCADE, -- Name of the rack (redundant for faster access)
    pos INTEGER NOT NULL, -- Position of the host in the rack
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_rack_position UNIQUE (rack_name, pos) -- Ensure unique position in the rack
);



CREATE TABLE subnets (
    subnet VARCHAR(255) PRIMARY KEY, -- Subnet address
    service_name VARCHAR(255) NOT NULL REFERENCES services(name) ON UPDATE CASCADE, -- Name of the service (redundant for faster access)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- set up mock data --
INSERT INTO users (username, password, role) VALUES ('admin', '123', 'admin') ON CONFLICT DO NOTHING;
INSERT INTO users (username, password, role) VALUES ('user1', '123', 'normal') ON CONFLICT DO NOTHING;
INSERT INTO users (username, password, role) VALUES ('user2', '123', 'normal') ON CONFLICT DO NOTHING;
INSERT INTO users (username, password, role) VALUES ('user3', '123', 'normal') ON CONFLICT DO NOTHING;
INSERT INTO services (name, username) VALUES ('nginx-proxy-a', 'user1') ON CONFLICT DO NOTHING;
INSERT INTO services (name, username) VALUES ('auth-service-b', 'user1') ON CONFLICT DO NOTHING;
INSERT INTO services (name, username) VALUES ('palworld-server-a', 'user2') ON CONFLICT DO NOTHING;
INSERT INTO services (name, username) VALUES ('web-hosting-service', 'user2') ON CONFLICT DO NOTHING;
INSERT INTO datacenters (name, height) VALUES ('TAIPEI-A1', 60) ON CONFLICT DO NOTHING;
INSERT INTO datacenters (name, height) VALUES ('TAIPEI-C2', 60) ON CONFLICT DO NOTHING;
INSERT INTO datacenters (name, height) VALUES ('TOKYO-A1', 60) ON CONFLICT DO NOTHING;
INSERT INTO datacenters (name, height) VALUES ('SEATTLE-B2', 60) ON CONFLICT DO NOTHING;
INSERT INTO rooms (name, height, dc_name) VALUES ('TPE1-ROOM-101', 60, 'TAIPEI-A1') ON CONFLICT DO NOTHING;
INSERT INTO rooms (name, height, dc_name) VALUES ('TPE1-ROOM-102', 60, 'TAIPEI-A1') ON CONFLICT DO NOTHING;
INSERT INTO rooms (name, height, dc_name) VALUES ('TPE1-ROOM-103', 60, 'TAIPEI-A1') ON CONFLICT DO NOTHING;
INSERT INTO rooms (name, height, dc_name) VALUES ('TPE2-ROOM-101', 60, 'TAIPEI-C2') ON CONFLICT DO NOTHING;
INSERT INTO rooms (name, height, dc_name) VALUES ('TPE2-ROOM-102', 60, 'TAIPEI-C2') ON CONFLICT DO NOTHING;
INSERT INTO rooms (name, height, dc_name) VALUES ('TYO1-ROOM-101', 60, 'TOKYO-A1') ON CONFLICT DO NOTHING;
INSERT INTO rooms (name, height, dc_name) VALUES ('TYO1-ROOM-102', 60, 'TOKYO-A1') ON CONFLICT DO NOTHING;
INSERT INTO rooms (name, height, dc_name) VALUES ('TYO1-ROOM-103', 60, 'TOKYO-A1') ON CONFLICT DO NOTHING;
INSERT INTO rooms (name, height, dc_name) VALUES ('TYO1-ROOM-104', 60, 'TOKYO-A1') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE1-R101-RACK-1', 60, 'auth-service-b', 'TAIPEI-A1', 'TPE1-ROOM-101') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE1-R101-RACK-2', 60, NULL, 'TAIPEI-A1', 'TPE1-ROOM-101') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE1-R101-RACK-3', 60, NULL, 'TAIPEI-A1', 'TPE1-ROOM-101') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE1-R101-RACK-4', 60, NULL, 'TAIPEI-A1', 'TPE1-ROOM-101') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE1-R102-RACK-1', 42, NULL, 'TAIPEI-A1', 'TPE1-ROOM-102') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE1-R102-RACK-2', 42, NULL, 'TAIPEI-A1', 'TPE1-ROOM-102') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE1-R102-RACK-3', 42, 'web-hosting-service', 'TAIPEI-A1', 'TPE1-ROOM-102') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE1-R103-RACK-1', 60, 'auth-service-b', 'TAIPEI-A1', 'TPE1-ROOM-103') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE1-R103-RACK-2', 60, 'nginx-proxy-a', 'TAIPEI-A1', 'TPE1-ROOM-103') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE1-R103-RACK-3', 60, 'auth-service-b', 'TAIPEI-A1', 'TPE1-ROOM-103') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE1-R103-RACK-4', 60, 'nginx-proxy-a', 'TAIPEI-A1', 'TPE1-ROOM-103') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE1-R103-RACK-5', 60, NULL, 'TAIPEI-A1', 'TPE1-ROOM-103') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE2-R101-RACK-1', 42, NULL, 'TAIPEI-C2', 'TPE2-ROOM-101') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE2-R101-RACK-2', 42, 'web-hosting-service', 'TAIPEI-C2', 'TPE2-ROOM-101') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE2-R101-RACK-3', 42, NULL, 'TAIPEI-C2', 'TPE2-ROOM-101') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE2-R102-RACK-1', 42, NULL, 'TAIPEI-C2', 'TPE2-ROOM-102') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE2-R102-RACK-2', 42, 'palworld-server-a', 'TAIPEI-C2', 'TPE2-ROOM-102') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE2-R102-RACK-3', 42, NULL, 'TAIPEI-C2', 'TPE2-ROOM-102') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TPE2-R102-RACK-4', 42, 'palworld-server-a', 'TAIPEI-C2', 'TPE2-ROOM-102') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TYO1-R101-RACK-1', 60, 'auth-service-b', 'TOKYO-A1', 'TYO1-ROOM-101') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TYO1-R102-RACK-1', 42, 'auth-service-b', 'TOKYO-A1', 'TYO1-ROOM-102') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TYO1-R102-RACK-2', 42, 'web-hosting-service', 'TOKYO-A1', 'TYO1-ROOM-102') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TYO1-R104-RACK-1', 60, 'palworld-server-a', 'TOKYO-A1', 'TYO1-ROOM-104') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TYO1-R104-RACK-2', 60, 'auth-service-b', 'TOKYO-A1', 'TYO1-ROOM-104') ON CONFLICT DO NOTHING;
INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES ('TYO1-R104-RACK-3', 60, 'palworld-server-a', 'TOKYO-A1', 'TYO1-ROOM-104') ON CONFLICT DO NOTHING;
INSERT INTO subnets (subnet, service_name) VALUES ('192.168.8.0/30', 'nginx-proxy-a') ON CONFLICT DO NOTHING;
INSERT INTO subnets (subnet, service_name) VALUES ('192.168.199.0/26', 'auth-service-b') ON CONFLICT DO NOTHING;
INSERT INTO subnets (subnet, service_name) VALUES ('192.168.10.0/30', 'palworld-server-a') ON CONFLICT DO NOTHING;
INSERT INTO subnets (subnet, service_name) VALUES ('192.168.11.0/30', 'palworld-server-a') ON CONFLICT DO NOTHING;
INSERT INTO subnets (subnet, service_name) VALUES ('192.168.100.128/28', 'web-hosting-service') ON CONFLICT DO NOTHING;
INSERT INTO subnets (subnet, service_name) VALUES ('172.36.40.0/30', 'web-hosting-service') ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.8.0', 'nginx-proxy-a', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.8.1', 'nginx-proxy-a', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.8.2', 'nginx-proxy-a', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.8.3', 'nginx-proxy-a', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.0', 'auth-service-b', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.1', 'auth-service-b', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.2', 'auth-service-b', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.3', 'auth-service-b', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.4', 'auth-service-b', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.5', 'auth-service-b', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.6', 'auth-service-b', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.7', 'auth-service-b', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.8', 'auth-service-b', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.9', 'auth-service-b', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.10', 'auth-service-b', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.11', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.12', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.13', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.14', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.15', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.16', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.17', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.18', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.19', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.20', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.21', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.22', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.23', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.24', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.25', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.26', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.27', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.28', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.29', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.30', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.31', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.32', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.33', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.34', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.35', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.36', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.37', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.38', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.39', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.40', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.41', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.42', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.43', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.44', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.45', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.46', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.47', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.48', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.49', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.50', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.51', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.52', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.53', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.54', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.55', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.56', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.57', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.58', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.59', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.60', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.61', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.62', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.199.63', 'auth-service-b', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.10.0', 'palworld-server-a', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.10.1', 'palworld-server-a', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.10.2', 'palworld-server-a', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.10.3', 'palworld-server-a', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.11.0', 'palworld-server-a', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.11.1', 'palworld-server-a', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.11.2', 'palworld-server-a', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.11.3', 'palworld-server-a', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.128', 'web-hosting-service', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.129', 'web-hosting-service', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.130', 'web-hosting-service', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.131', 'web-hosting-service', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.132', 'web-hosting-service', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.133', 'web-hosting-service', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.134', 'web-hosting-service', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.135', 'web-hosting-service', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.136', 'web-hosting-service', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.137', 'web-hosting-service', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.138', 'web-hosting-service', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.139', 'web-hosting-service', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.140', 'web-hosting-service', true) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.141', 'web-hosting-service', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.142', 'web-hosting-service', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('192.168.100.143', 'web-hosting-service', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('172.36.40.0', 'web-hosting-service', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('172.36.40.1', 'web-hosting-service', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('172.36.40.2', 'web-hosting-service', false) ON CONFLICT DO NOTHING;
INSERT INTO IPs (ip, service_name, assigned) VALUES ('172.36.40.3', 'web-hosting-service', false) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('nginx-proxy-a-host-1', 2, '192.168.8.0', true, 'nginx-proxy-a', 'TAIPEI-A1', 'TPE1-ROOM-103', 'TPE1-R103-RACK-4', 1) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('nginx-proxy-a-host-2', 3, '192.168.8.1', true, 'nginx-proxy-a', 'TAIPEI-A1', 'TPE1-ROOM-103', 'TPE1-R103-RACK-4', 3) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('nginx-proxy-a-host-3', 2, '192.168.8.2', true, 'nginx-proxy-a', 'TAIPEI-A1', 'TPE1-ROOM-103', 'TPE1-R103-RACK-4', 6) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('nginx-proxy-a-host-4', 4, '192.168.8.3', true, 'nginx-proxy-a', 'TAIPEI-A1', 'TPE1-ROOM-103', 'TPE1-R103-RACK-4', 8) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-1', 1, '192.168.199.0', true, 'auth-service-b', 'TAIPEI-A1', 'TPE1-ROOM-101', 'TPE1-R101-RACK-1', 1) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-2', 2, '192.168.199.1', true, 'auth-service-b', 'TAIPEI-A1', 'TPE1-ROOM-101', 'TPE1-R101-RACK-1', 2) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-3', 2, '192.168.199.2', true, 'auth-service-b', 'TAIPEI-A1', 'TPE1-ROOM-101', 'TPE1-R101-RACK-1', 4) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-4', 1, '192.168.199.3', true, 'auth-service-b', 'TAIPEI-A1', 'TPE1-ROOM-101', 'TPE1-R101-RACK-1', 6) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-5', 4, '192.168.199.4', true, 'auth-service-b', 'TAIPEI-A1', 'TPE1-ROOM-103', 'TPE1-R103-RACK-1', 1) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-6', 2, '192.168.199.5', true, 'auth-service-b', 'TAIPEI-A1', 'TPE1-ROOM-103', 'TPE1-R103-RACK-1', 5) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-7', 1, '192.168.199.6', true, 'auth-service-b', 'TAIPEI-A1', 'TPE1-ROOM-103', 'TPE1-R103-RACK-1', 7) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-8', 3, '192.168.199.7', true, 'auth-service-b', 'TAIPEI-A1', 'TPE1-ROOM-103', 'TPE1-R103-RACK-1', 8) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-9', 3, '192.168.199.8', true, 'auth-service-b', 'TOKYO-A1', 'TYO1-ROOM-101', 'TYO1-R101-RACK-1', 1) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-10', 1, '192.168.199.9', true, 'auth-service-b', 'TOKYO-A1', 'TYO1-ROOM-101', 'TYO1-R101-RACK-1', 4) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-11', 2, '192.168.199.10', true, 'auth-service-b', 'TOKYO-A1', 'TYO1-ROOM-102', 'TYO1-R102-RACK-1', 1) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-12', 4, NULL, false, 'auth-service-b', 'TOKYO-A1', 'TYO1-ROOM-102', 'TYO1-R102-RACK-1', 3) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-13', 4, NULL, false, 'auth-service-b', 'TOKYO-A1', 'TYO1-ROOM-102', 'TYO1-R102-RACK-1', 7) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-14', 4, NULL, false, 'auth-service-b', 'TOKYO-A1', 'TYO1-ROOM-102', 'TYO1-R102-RACK-1', 11) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-15', 4, NULL, false, 'auth-service-b', 'TOKYO-A1', 'TYO1-ROOM-102', 'TYO1-R102-RACK-1', 15) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-16', 4, NULL, false, 'auth-service-b', 'TOKYO-A1', 'TYO1-ROOM-102', 'TYO1-R102-RACK-1', 19) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-17', 4, NULL, false, 'auth-service-b', 'TOKYO-A1', 'TYO1-ROOM-102', 'TYO1-R102-RACK-1', 23) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-18', 4, NULL, false, 'auth-service-b', 'TOKYO-A1', 'TYO1-ROOM-102', 'TYO1-R102-RACK-1', 27) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-19', 4, NULL, false, 'auth-service-b', 'TOKYO-A1', 'TYO1-ROOM-102', 'TYO1-R102-RACK-1', 31) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('auth-service-b-host-20', 4, NULL, false, 'auth-service-b', 'TOKYO-A1', 'TYO1-ROOM-102', 'TYO1-R102-RACK-1', 35) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('palworld-server-a-host-1', 1, '192.168.10.0', true, 'palworld-server-a', 'TAIPEI-C2', 'TPE2-ROOM-102', 'TPE2-R102-RACK-2', 1) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('palworld-server-a-host-2', 4, '192.168.10.1', true, 'palworld-server-a', 'TAIPEI-C2', 'TPE2-ROOM-102', 'TPE2-R102-RACK-2', 2) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('palworld-server-a-host-3', 2, '192.168.10.2', true, 'palworld-server-a', 'TAIPEI-C2', 'TPE2-ROOM-102', 'TPE2-R102-RACK-4', 1) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('palworld-server-a-host-4', 4, '192.168.10.3', true, 'palworld-server-a', 'TAIPEI-C2', 'TPE2-ROOM-102', 'TPE2-R102-RACK-4', 3) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('palworld-server-a-host-5', 1, '192.168.11.0', true, 'palworld-server-a', 'TAIPEI-C2', 'TPE2-ROOM-102', 'TPE2-R102-RACK-4', 7) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('palworld-server-a-host-6', 1, '192.168.11.1', true, 'palworld-server-a', 'TAIPEI-C2', 'TPE2-ROOM-102', 'TPE2-R102-RACK-4', 8) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('palworld-server-a-host-7', 3, '192.168.11.2', true, 'palworld-server-a', 'TOKYO-A1', 'TYO1-ROOM-104', 'TYO1-R104-RACK-1', 1) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('palworld-server-a-host-8', 4, '192.168.11.3', true, 'palworld-server-a', 'TOKYO-A1', 'TYO1-ROOM-104', 'TYO1-R104-RACK-1', 4) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('web-hosting-service-host-1', 1, '192.168.100.128', true, 'web-hosting-service', 'TAIPEI-A1', 'TPE1-ROOM-102', 'TPE1-R102-RACK-3', 1) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('web-hosting-service-host-2', 1, '192.168.100.129', true, 'web-hosting-service', 'TAIPEI-A1', 'TPE1-ROOM-102', 'TPE1-R102-RACK-3', 2) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('web-hosting-service-host-3', 3, '192.168.100.130', true, 'web-hosting-service', 'TAIPEI-A1', 'TPE1-ROOM-102', 'TPE1-R102-RACK-3', 3) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('web-hosting-service-host-4', 4, '192.168.100.131', true, 'web-hosting-service', 'TAIPEI-A1', 'TPE1-ROOM-102', 'TPE1-R102-RACK-3', 6) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('web-hosting-service-host-5', 1, '192.168.100.132', true, 'web-hosting-service', 'TAIPEI-A1', 'TPE1-ROOM-102', 'TPE1-R102-RACK-3', 10) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('web-hosting-service-host-6', 1, '192.168.100.133', true, 'web-hosting-service', 'TAIPEI-C2', 'TPE2-ROOM-101', 'TPE2-R101-RACK-2', 1) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('web-hosting-service-host-7', 2, '192.168.100.134', true, 'web-hosting-service', 'TAIPEI-C2', 'TPE2-ROOM-101', 'TPE2-R101-RACK-2', 2) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('web-hosting-service-host-8', 3, '192.168.100.135', true, 'web-hosting-service', 'TAIPEI-C2', 'TPE2-ROOM-101', 'TPE2-R101-RACK-2', 4) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('web-hosting-service-host-9', 4, '192.168.100.136', true, 'web-hosting-service', 'TAIPEI-C2', 'TPE2-ROOM-101', 'TPE2-R101-RACK-2', 7) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('web-hosting-service-host-10', 2, '192.168.100.137', true, 'web-hosting-service', 'TOKYO-A1', 'TYO1-ROOM-102', 'TYO1-R102-RACK-2', 1) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('web-hosting-service-host-11', 3, '192.168.100.138', true, 'web-hosting-service', 'TOKYO-A1', 'TYO1-ROOM-102', 'TYO1-R102-RACK-2', 3) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('web-hosting-service-host-12', 1, '192.168.100.139', true, 'web-hosting-service', 'TOKYO-A1', 'TYO1-ROOM-102', 'TYO1-R102-RACK-2', 6) ON CONFLICT DO NOTHING;
INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES ('web-hosting-service-host-13', 4, '192.168.100.140', true, 'web-hosting-service', 'TOKYO-A1', 'TYO1-ROOM-102', 'TYO1-R102-RACK-2', 7) ON CONFLICT DO NOTHING;
