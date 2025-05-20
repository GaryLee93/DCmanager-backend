-- CREATE DATABASE datacenter_management;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

------------------------------------------------------------
-------------  Table Creation and Constraints --------------
------------------------------------------------------------

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

-- Table for services
-- Todo: dc link
CREATE TABLE services (
    name VARCHAR(255) PRIMARY KEY, -- Name of the service
    subnet VARCHAR(255) NOT NULL, -- Subnet for the service
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for racks, linked to rooms, datacenters, and services
CREATE TABLE racks (
    name VARCHAR(255) PRIMARY KEY, -- Name of the rack
    height INTEGER NOT NULL, -- Height of the rack
    service_name VARCHAR(255) NOT NULL REFERENCES services(name) ON UPDATE CASCADE, -- Name of the service (redundant for faster access)
    dc_name VARCHAR(255) NOT NULL REFERENCES datacenters(name) ON UPDATE CASCADE, -- Name of the datacenter (redundant for faster access)
    room_name VARCHAR(255) NOT NULL REFERENCES rooms(name) ON UPDATE CASCADE, -- Name of the room (redundant for faster access)
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
    dc_name VARCHAR(255) NOT NULL REFERENCES datacenters(name) ON UPDATE CASCADE, -- Name of the datacenter (redundant for faster access)
    room_name VARCHAR(255) NOT NULL REFERENCES rooms(name) ON UPDATE CASCADE, -- Name of the room (redundant for faster access)
    rack_name VARCHAR(255) NOT NULL REFERENCES racks(name) ON UPDATE CASCADE, -- Name of the rack (redundant for faster access)
    pos INTEGER NOT NULL, -- Position of the host in the rack
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_rack_position UNIQUE (rack_id, pos) -- Ensure unique position in the rack
);

-- Table for users, with permissions
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) NOT NULL UNIQUE, -- Unique username
    password VARCHAR(255) NOT NULL, -- Password (hashed)
    role VARCHAR(50) NOT NULL CHECK (role IN ('normal', 'manager')), -- User role (changed from permission to role)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
