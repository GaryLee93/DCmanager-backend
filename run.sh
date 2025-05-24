#!/bin/bash

echo "Creating Docker network..."
docker network create dcmanager-network 2>/dev/null || true

echo "Building database image..."
cd db
docker buildx build -t dcmanager-db .

echo "Building backend image..."
cd ..
docker buildx build -t dcmanager-backend .

echo "Build complete!"

echo "Stopping existing containers if running..."
docker stop dcmanager-db dcmanager-backend 2>/dev/null || true
docker rm dcmanager-db dcmanager-backend 2>/dev/null || true

echo "Ensuring network exists..."
docker network create dcmanager-network 2>/dev/null || true

echo "Starting database container..."
docker run -d \
  --name dcmanager-db \
  --network dcmanager-network \
  -p 5432:5432 \
  -v dcmanager-db-data:/var/lib/postgresql/data \
  dcmanager-db

echo "Waiting for database to initialize..."
sleep 5

echo "Starting backend container..."
docker run -d \
  --name dcmanager-backend \
  --network dcmanager-network \
  -p 5000:5000 \
  -e DB_HOST=dcmanager-db \
  -e DB_PORT=5432 \
  -e DB_NAME=datacenter_management \
  -e DB_USER=postgres \
  -e DB_PASSWORD=postgres \
  dcmanager-backend

echo "Containers started!"
echo "Backend available at: http://localhost:5000"
echo "Database available at: localhost:5432"
echo ""
echo "To view logs:"
echo "  docker logs dcmanager-backend"
echo "  docker logs dcmanager-db"
