#!/bin/bash

# Start Redis for Celery broker
# Assumes Docker is installed and running.

CONTAINER_NAME="redis-rag"
IMAGE="redis:alpine"
PORT=6379

echo "Starting Redis container: $CONTAINER_NAME on port $PORT"

# Check if container already exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Container $CONTAINER_NAME already exists. Removing it first."
    docker rm -f $CONTAINER_NAME
fi

# Run Redis
docker run -d \
    --name $CONTAINER_NAME \
    -p $PORT:6379 \
    $IMAGE

echo "Redis started. Waiting for it to be ready..."
sleep 5

# Test connection
if docker exec $CONTAINER_NAME redis-cli ping | grep -q "PONG"; then
    echo "Redis is ready at redis://localhost:$PORT"
else
    echo "Failed to connect to Redis. Check logs: docker logs $CONTAINER_NAME"
    exit 1
fi