#!/bin/bash

# Start MongoDB for RAG-22 project
# This script starts MongoDB using Docker and waits for it to be ready

set -e

CONTAINER_NAME="mongo-rag22"
IMAGE="mongodb/mongodb-community-server:7.0-ubi8"
PORT=27017
DB_NAME="ragdb"

echo "🚀 Starting MongoDB for RAG-22 project..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if container already exists and is running
if docker ps --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "✅ MongoDB container is already running"
    exit 0
fi

# Check if container exists but is stopped
if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "📦 Found existing MongoDB container. Starting it..."
    docker start $CONTAINER_NAME
else
    echo "📦 Creating new MongoDB container..."
    # Run MongoDB with authentication disabled for development
    docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:27017 \
        -v mongo-rag22-data:/data/db \
        $IMAGE \
        --bind_ip_all
fi

echo "⏳ Waiting for MongoDB to be ready..."
timeout=30
counter=0

while [ $counter -lt $timeout ]; do
    if docker exec $CONTAINER_NAME mongosh --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; then
        echo "✅ MongoDB is ready!"
        
        # Create the database and a test collection
        echo "📊 Setting up database '$DB_NAME'..."
        docker exec $CONTAINER_NAME mongosh --eval "
            use $DB_NAME;
            db.createCollection('documents');
            db.createCollection('chunks');
            print('Database $DB_NAME created successfully');
        " --quiet
        
        echo "🎉 MongoDB setup complete!"
        echo "📍 Connection string: mongodb://localhost:$PORT"
        echo "📊 Database: $DB_NAME"
        echo ""
        echo "To stop MongoDB: docker stop $CONTAINER_NAME"
        echo "To remove MongoDB: docker rm -f $CONTAINER_NAME && docker volume rm mongo-rag22-data"
        exit 0
    fi
    
    sleep 1
    counter=$((counter + 1))
done

echo "❌ MongoDB failed to start within $timeout seconds"
echo "📋 Container logs:"
docker logs $CONTAINER_NAME
exit 1