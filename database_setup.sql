-- CREATE DATABASE datacenter_management;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

------------------------------------------------------------
-------------  Table Creation and Constraints --------------
------------------------------------------------------------

-- Table for datacenters, storing basic information and statistics
CREATE TABLE datacenters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    default_height INTEGER,
    n_rooms INTEGER DEFAULT 0, -- Number of rooms in the datacenter
    n_racks INTEGER DEFAULT 0, -- Number of racks in the datacenter
    n_hosts INTEGER DEFAULT 0, -- Number of hosts in the datacenter
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for rooms, linked to datacenters
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    height INTEGER NOT NULL, -- Height of the room
    n_racks INTEGER DEFAULT 0, -- Number of racks in the room
    n_hosts INTEGER DEFAULT 0, -- Number of hosts in the room
    dc_id UUID NOT NULL REFERENCES datacenters(id) ON DELETE CASCADE, -- Foreign key to datacenters
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for racks, linked to rooms and datacenters
CREATE TABLE racks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    height INTEGER NOT NULL, -- Height of the rack
    n_hosts INTEGER DEFAULT 0, -- Number of hosts in the rack
    dc_id UUID NOT NULL REFERENCES datacenters(id) ON DELETE CASCADE, -- Foreign key to datacenters
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE, -- Foreign key to rooms
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT height_check CHECK (height >= 18) -- Ensure rack height is at least 18
);

-- Table for IP subnets
CREATE TABLE ip_subnets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ip CIDR NOT NULL, -- IP range in CIDR format
    mask INTEGER NOT NULL CHECK (mask >= 0 AND mask <= 32), -- Subnet mask validation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for company IP ranges
CREATE TABLE company_ip_ranges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    start_ip INET NOT NULL, -- Start of the IP range
    end_ip INET NOT NULL, -- End of the IP range
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_range CHECK (start_ip <= end_ip) -- Ensure start IP is less than or equal to end IP
);

-- Table for services, linked to IP subnets
CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL, -- Name of the service
    subnet_id UUID REFERENCES ip_subnets(id) ON DELETE SET NULL, -- Foreign key to IP subnets
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for hosts, linked to racks, rooms, datacenters, and services
CREATE TABLE hosts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL, -- Name of the host
    height INTEGER NOT NULL CHECK (height >= 1 AND height <= 4), -- Height of the host (1-4 units)
    ip INET, -- IP address of the host
    service_id UUID REFERENCES services(id) ON DELETE SET NULL, -- Foreign key to services
    dc_id UUID NOT NULL REFERENCES datacenters(id) ON DELETE CASCADE, -- Foreign key to datacenters
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE, -- Foreign key to rooms
    rack_id UUID NOT NULL REFERENCES racks(id) ON DELETE CASCADE, -- Foreign key to racks
    rack_position INTEGER NOT NULL, -- Position of the host in the rack
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_rack_position UNIQUE (rack_id, rack_position) -- Ensure unique position in the rack
);

-- Table for users, with permissions
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) NOT NULL UNIQUE, -- Unique username
    password VARCHAR(255) NOT NULL, -- Password (hashed)
    permission VARCHAR(50) NOT NULL CHECK (permission IN ('normal', 'manager')), -- User role
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for mapping services to hosts
CREATE TABLE service_hosts (
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE, -- Foreign key to services
    host_id UUID NOT NULL REFERENCES hosts(id) ON DELETE CASCADE, -- Foreign key to hosts
    PRIMARY KEY (service_id, host_id), -- Composite primary key
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

------------------------------------------------------------
-------------  Function and Trigger Creation ---------------
------------------------------------------------------------

-- Function to validate that a rack's height does not exceed its room's height
CREATE OR REPLACE FUNCTION validate_rack_height()
RETURNS TRIGGER AS $$
DECLARE
    room_height INTEGER;
BEGIN
    SELECT height INTO room_height FROM rooms WHERE id = NEW.room_id;
    IF NEW.height > room_height THEN
        RAISE EXCEPTION 'racks height must not exceed rooms height (racks height: %, rooms height: %)', NEW.height, room_height;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to enforce rack height validation before insert or update
CREATE TRIGGER before_rack_insert_update
BEFORE INSERT OR UPDATE ON racks
FOR EACH ROW EXECUTE FUNCTION validate_rack_height();

-- Function to update the number of hosts in a rack
CREATE OR REPLACE FUNCTION update_rack_host_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE racks SET n_hosts = n_hosts + 1 WHERE id = NEW.rack_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE racks SET n_hosts = n_hosts - 1 WHERE id = OLD.rack_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.rack_id != NEW.rack_id THEN
        UPDATE racks SET n_hosts = n_hosts - 1 WHERE id = OLD.rack_id;
        UPDATE racks SET n_hosts = n_hosts + 1 WHERE id = NEW.rack_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update rack host count after insert, update, or delete on hosts
CREATE TRIGGER hosts_after_insert_update_delete
AFTER INSERT OR UPDATE OR DELETE ON hosts
FOR EACH ROW EXECUTE FUNCTION update_rack_host_count();

-- Function to update the number of racks in a room
CREATE OR REPLACE FUNCTION update_room_rack_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE rooms SET n_racks = n_racks + 1 WHERE id = NEW.room_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE rooms SET n_racks = n_racks - 1 WHERE id = OLD.room_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.room_id != NEW.room_id THEN
        UPDATE rooms SET n_racks = n_racks - 1 WHERE id = OLD.room_id;
        UPDATE rooms SET n_racks = n_racks + 1 WHERE id = NEW.room_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update room rack count after insert, update, or delete on racks
CREATE TRIGGER racks_after_insert_update_delete
AFTER INSERT OR UPDATE OR DELETE ON racks
FOR EACH ROW EXECUTE FUNCTION update_room_rack_count();

-- Additional functions and triggers follow similar patterns...
CREATE OR REPLACE FUNCTION update_room_host_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE rooms SET n_hosts = n_hosts + 1 WHERE id = NEW.room_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE rooms SET n_hosts = n_hosts - 1 WHERE id = OLD.room_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.room_id != NEW.room_id THEN
        UPDATE rooms SET n_hosts = n_hosts - 1 WHERE id = OLD.room_id;
        UPDATE rooms SET n_hosts = n_hosts + 1 WHERE id = NEW.room_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER hosts_room_after_insert_update_delete
AFTER INSERT OR UPDATE OR DELETE ON hosts
FOR EACH ROW EXECUTE FUNCTION update_room_host_count();

CREATE OR REPLACE FUNCTION update_dc_room_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE datacenters SET n_rooms = n_rooms + 1 WHERE id = NEW.dc_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE datacenters SET n_rooms = n_rooms - 1 WHERE id = OLD.dc_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.dc_id != NEW.dc_id THEN
        UPDATE datacenters SET n_rooms = n_rooms - 1 WHERE id = OLD.dc_id;
        UPDATE datacenters SET n_rooms = n_rooms + 1 WHERE id = NEW.dc_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER rooms_after_insert_update_delete
AFTER INSERT OR UPDATE OR DELETE ON rooms
FOR EACH ROW EXECUTE FUNCTION update_dc_room_count();

CREATE OR REPLACE FUNCTION update_dc_counts()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE datacenters d SET 
        n_racks = (SELECT COUNT(*) FROM racks WHERE dc_id = d.id),
        n_hosts = (SELECT COUNT(*) FROM hosts WHERE dc_id = d.id);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- sync datacenter counts after any change in hosts or racks
CREATE TRIGGER sync_dc_counts
AFTER INSERT OR UPDATE OR DELETE ON hosts
FOR EACH STATEMENT EXECUTE FUNCTION update_dc_counts();

-- if a rack's room changes, update the hosts' room_id
-- In theory, this should not be need, because ID shoud not change
CREATE OR REPLACE FUNCTION update_hosts_room_id()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND OLD.room_id != NEW.room_id THEN
        UPDATE hosts SET room_id = NEW.room_id WHERE rack_id = NEW.id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER rack_room_change_trigger
AFTER UPDATE ON racks
FOR EACH ROW EXECUTE FUNCTION update_hosts_room_id();

-- create indexes for faster lookups
CREATE INDEX idx_rooms_dc_id ON rooms(dc_id);
CREATE INDEX idx_racks_room_id ON racks(room_id);
CREATE INDEX idx_racks_dc_id ON racks(dc_id);
CREATE INDEX idx_hosts_rack_id ON hosts(rack_id);
CREATE INDEX idx_hosts_room_id ON hosts(room_id);
CREATE INDEX idx_hosts_dc_id ON hosts(dc_id);
CREATE INDEX idx_hosts_service_id ON hosts(service_id);
CREATE INDEX idx_service_hosts_service_id ON service_hosts(service_id);
CREATE INDEX idx_service_hosts_host_id ON service_hosts(host_id);