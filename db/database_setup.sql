-- CREATE DATABASE datacenter_management;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

------------------------------------------------------------
-------------  Table Creation and Constraints --------------
------------------------------------------------------------

-- Table for datacenters, storing basic information and statistics
CREATE TABLE datacenters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    height INTEGER NOT NULL, -- Height of the datacenter
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
    dc_name VARCHAR(255) NOT NULL REFERENCES datacenters(name) ON UPDATE CASCADE, -- Name of the datacenter (redundant for faster access)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for services
CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL, -- Name of the service
    n_racks INTEGER DEFAULT 0, -- Number of racks assigned to service
    n_hosts INTEGER DEFAULT 0, -- Number of hosts in the service
    total_ip INTEGER DEFAULT 0, -- Total IPs allocated to this service
    available_ip INTEGER DEFAULT 0, -- Available IPs for this service
    dc_name VARCHAR(255) NOT NULL REFERENCES datacenters(name) ON UPDATE CASCADE, -- Name of the datacenter (redundant for faster access)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for racks, linked to rooms, datacenters, and services
CREATE TABLE racks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    height INTEGER NOT NULL, -- Height of the rack
    capacity INTEGER NOT NULL, -- Remaining capacity of the rack
    n_hosts INTEGER DEFAULT 0, -- Number of hosts in the rack
    service_name VARCHAR(255), -- Name of the service (redundant for faster access)
    dc_name VARCHAR(255) NOT NULL REFERENCES datacenters(name) ON UPDATE CASCADE, -- Name of the datacenter (redundant for faster access)
    room_name VARCHAR(255) NOT NULL REFERENCES rooms(name) ON UPDATE CASCADE, -- Name of the room (redundant for faster access)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for company IP ranges
CREATE TABLE ip_ranges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dc_id UUID NOT NULL REFERENCES datacenters(id) ON DELETE CASCADE, -- Foreign key to datacenters
    start_ip INET NOT NULL, -- Start of the IP range
    end_ip INET NOT NULL, -- End of the IP range
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_range CHECK (start_ip <= end_ip) -- Ensure start IP is less than or equal to end IP
);

-- Table for service IPs
CREATE TABLE service_ips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ip INET NOT NULL, -- IP address
    dc_name VARCHAR(255) NOT NULL REFERENCES datacenters(name) ON UPDATE CASCADE, -- Name of the datacenter (redundant for faster access)
    service_
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE, -- Foreign key to services
    assigned BOOLEAN DEFAULT FALSE, -- Whether this IP is assigned to a host
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for hosts, linked to racks, rooms, datacenters, and services
CREATE TABLE hosts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL, -- Name of the host
    height INTEGER NOT NULL CHECK (height >= 1 AND height <= 4), -- Height of the host (1-4 units)
    ip INET, -- IP address of the host
    running BOOLEAN DEFAULT FALSE, -- Whether the host is running
    service_id UUID REFERENCES services(id) ON DELETE SET NULL, -- Foreign key to services
    service_name VARCHAR(255), -- Name of the service (redundant for faster access)
    dc_id UUID NOT NULL REFERENCES datacenters(id) ON DELETE CASCADE, -- Foreign key to datacenters
    dc_name VARCHAR(255) NOT NULL REFERENCES datacenters(name) ON UPDATE CASCADE, -- Name of the datacenter (redundant for faster access)
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE, -- Foreign key to rooms
    room_name VARCHAR(255) NOT NULL REFERENCES rooms(name) ON UPDATE CASCADE, -- Name of the room (redundant for faster access)
    rack_id UUID NOT NULL REFERENCES racks(id) ON DELETE CASCADE, -- Foreign key to racks
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
        RAISE EXCEPTION 'rack height must not exceed room height (rack height: %, room height: %)', NEW.height, room_height;
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

-- Function to update the number of hosts in a room
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

-- Trigger to update room host count after insert, update, or delete on hosts
CREATE TRIGGER hosts_room_after_insert_update_delete
AFTER INSERT OR UPDATE OR DELETE ON hosts
FOR EACH ROW EXECUTE FUNCTION update_room_host_count();

-- Function to update the number of rooms in a datacenter
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

-- Trigger to update datacenter room count after insert, update, or delete on rooms
CREATE TRIGGER rooms_after_insert_update_delete
AFTER INSERT OR UPDATE OR DELETE ON rooms
FOR EACH ROW EXECUTE FUNCTION update_dc_room_count();

-- Function to update datacenter counts
CREATE OR REPLACE FUNCTION update_dc_counts()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE datacenters d SET 
        n_racks = (SELECT COUNT(*) FROM racks WHERE dc_id = d.id),
        n_hosts = (SELECT COUNT(*) FROM hosts WHERE dc_id = d.id);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Sync datacenter counts after any change in hosts or racks
CREATE TRIGGER sync_dc_counts
AFTER INSERT OR UPDATE OR DELETE ON hosts
FOR EACH STATEMENT EXECUTE FUNCTION update_dc_counts();

-- Function to update service rack count
CREATE OR REPLACE FUNCTION update_service_rack_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF NEW.service_id IS NOT NULL AND (OLD.service_id IS NULL OR OLD.service_id != NEW.service_id) THEN
            UPDATE services SET n_racks = n_racks + 1 WHERE id = NEW.service_id;
        END IF;
        IF OLD.service_id IS NOT NULL AND (NEW.service_id IS NULL OR OLD.service_id != NEW.service_id) THEN
            UPDATE services SET n_racks = n_racks - 1 WHERE id = OLD.service_id;
        END IF;
    ELSIF TG_OP = 'INSERT' AND NEW.service_id IS NOT NULL THEN
        UPDATE services SET n_racks = n_racks + 1 WHERE id = NEW.service_id;
    ELSIF TG_OP = 'DELETE' AND OLD.service_id IS NOT NULL THEN
        UPDATE services SET n_racks = n_racks - 1 WHERE id = OLD.service_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update service rack count after insert, update, or delete on racks
CREATE TRIGGER racks_service_after_insert_update_delete
AFTER INSERT OR UPDATE OR DELETE ON racks
FOR EACH ROW EXECUTE FUNCTION update_service_rack_count();

-- Function to update service host count
CREATE OR REPLACE FUNCTION update_service_host_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF NEW.service_id IS NOT NULL AND (OLD.service_id IS NULL OR OLD.service_id != NEW.service_id) THEN
            UPDATE services SET n_hosts = n_hosts + 1 WHERE id = NEW.service_id;
        END IF;
        IF OLD.service_id IS NOT NULL AND (NEW.service_id IS NULL OR OLD.service_id != NEW.service_id) THEN
            UPDATE services SET n_hosts = n_hosts - 1 WHERE id = OLD.service_id;
        END IF;
    ELSIF TG_OP = 'INSERT' AND NEW.service_id IS NOT NULL THEN
        UPDATE services SET n_hosts = n_hosts + 1 WHERE id = NEW.service_id;
    ELSIF TG_OP = 'DELETE' AND OLD.service_id IS NOT NULL THEN
        UPDATE services SET n_hosts = n_hosts - 1 WHERE id = OLD.service_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update service host count after insert, update, or delete on hosts
CREATE TRIGGER hosts_service_after_insert_update_delete
AFTER INSERT OR UPDATE OR DELETE ON hosts
FOR EACH ROW EXECUTE FUNCTION update_service_host_count();

-- Function to verify IP assignment to hosts
CREATE OR REPLACE FUNCTION verify_ip_assignment()
RETURNS TRIGGER AS $$
DECLARE
    ip_service_id UUID;
BEGIN
    IF NEW.ip IS NOT NULL THEN
        -- Check if IP exists in service_ips
        SELECT service_id INTO ip_service_id FROM service_ips 
        WHERE ip = NEW.ip AND assigned = FALSE;
        
        IF ip_service_id IS NULL THEN
            RAISE EXCEPTION 'IP address % is not available for assignment', NEW.ip;
        END IF;
        
        IF NEW.service_id IS NULL OR NEW.service_id != ip_service_id THEN
            RAISE EXCEPTION 'IP address % does not belong to the specified service', NEW.ip;
        END IF;
        
        -- Mark IP as assigned
        UPDATE service_ips SET assigned = TRUE WHERE ip = NEW.ip;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to verify IP assignment before insert or update on hosts
CREATE TRIGGER before_host_ip_assignment
BEFORE INSERT OR UPDATE OF ip ON hosts
FOR EACH ROW WHEN (NEW.ip IS NOT NULL)
EXECUTE FUNCTION verify_ip_assignment();

-- Function to free IP when host is deleted or IP is changed
CREATE OR REPLACE FUNCTION free_ip()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' AND OLD.ip IS NOT NULL THEN
        UPDATE service_ips SET assigned = FALSE WHERE ip = OLD.ip;
    ELSIF TG_OP = 'UPDATE' AND OLD.ip IS NOT NULL AND (NEW.ip IS NULL OR OLD.ip != NEW.ip) THEN
        UPDATE service_ips SET assigned = FALSE WHERE ip = OLD.ip;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to free IP after delete or update on hosts
CREATE TRIGGER after_host_ip_change
AFTER DELETE OR UPDATE OF ip ON hosts
FOR EACH ROW EXECUTE FUNCTION free_ip();

-- Function to set host service_id based on rack's service_id if not specified
CREATE OR REPLACE FUNCTION set_host_service_id()
RETURNS TRIGGER AS $$
DECLARE
    rack_service_id UUID;
BEGIN
    IF NEW.service_id IS NULL THEN
        SELECT service_id INTO rack_service_id FROM racks WHERE id = NEW.rack_id;
        IF rack_service_id IS NOT NULL THEN
            NEW.service_id := rack_service_id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to set host service_id before insert or update
CREATE TRIGGER before_host_service_id
BEFORE INSERT OR UPDATE ON hosts
FOR EACH ROW EXECUTE FUNCTION set_host_service_id();

-- Create indexes for faster lookups
CREATE INDEX idx_rooms_dc_id ON rooms(dc_id);
CREATE INDEX idx_racks_room_id ON racks(room_id);
CREATE INDEX idx_racks_dc_id ON racks(dc_id);
CREATE INDEX idx_racks_service_id ON racks(service_id);
CREATE INDEX idx_hosts_room_id ON hosts(room_id);
CREATE INDEX idx_hosts_rack_id ON hosts(rack_id);
CREATE INDEX idx_hosts_dc_id ON hosts(dc_id);
CREATE INDEX idx_hosts_service_id ON hosts(service_id);
CREATE INDEX idx_service_ips_service_id ON service_ips(service_id);
CREATE INDEX idx_service_ips_ip ON service_ips(ip);
