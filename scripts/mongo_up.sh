#!/bin/bash

# Start MongoDB with vector search support (MongoDB 7.x)
# Assumes Docker is installed and running.

CONTAINER_NAME="mongo-rag"
IMAGE="mongodb/mongodb-community-server:7.0-ubi8"
PORT=27017

echo "Starting MongoDB container: $CONTAINER_NAME on port $PORT"

# Check if container already exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Container $CONTAINER_NAME already exists. Removing it first."
    docker rm -f $CONTAINER_NAME
fi

# Run MongoDB
docker run -d \
    --name $CONTAINER_NAME \
    -p $PORT:27017 \
    -e MONGO_INITDB_ROOT_USERNAME=admin \
    -e MONGO_INITDB_ROOT_PASSWORD=password \
    $IMAGE

echo "MongoDB started. Waiting for it to be ready..."
sleep 10

# Test connection
if docker exec $CONTAINER_NAME mongosh --eval "db.adminCommand('ping')" --quiet; then
    echo "MongoDB is ready at mongodb://admin:password@localhost:$PORT"
else
    echo "Failed to connect to MongoDB. Check logs: docker logs $CONTAINER_NAME"
    exit 1
fi