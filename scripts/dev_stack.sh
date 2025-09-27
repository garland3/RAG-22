#!/bin/bash

# Start the full development stack: MongoDB and Redis

echo "Starting development stack..."

# Start MongoDB
./scripts/mongo_up.sh

# Start Redis
./scripts/redis_up.sh

echo "Development stack is up!"
echo "MongoDB: mongodb://admin:password@localhost:27017"
echo "Redis: redis://localhost:6379"
echo ""
echo "To stop: docker stop mongo-rag redis-rag && docker rm mongo-rag redis-rag"