#!/bin/bash

# Installation script for RAG-22 project
# This script sets up the development environment with all dependencies

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_NAME=".venv"

echo "🚀 Setting up RAG-22 project environment..."
echo "📁 Project root: $PROJECT_ROOT"

# Check if Python 3.10+ is available
echo "🐍 Checking Python version..."
if command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$($python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$PYTHON_VERSION >= 3.10" | bc -l) -eq 1 ]]; then
        PYTHON_CMD="python3"
    else
        echo "❌ Python 3.10+ is required. Found: $PYTHON_VERSION"
        exit 1
    fi
else
    echo "❌ Python 3.10+ is not installed. Please install Python 3.10 or higher."
    exit 1
fi

echo "✅ Using Python: $PYTHON_CMD"

# Check if Docker is available
echo "🐳 Checking Docker availability..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Installation guide: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is available and running"

# Check if uv is available
echo "⚡ Checking uv availability..."
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first."
    echo "   Installation guide: https://github.com/astral-sh/uv#installation"
    exit 1
fi

echo "✅ uv is available"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_NAME" ]; then
    echo "📦 Creating virtual environment: $VENV_NAME"
    uv venv --python $PYTHON_CMD $VENV_NAME
else
    echo "✅ Virtual environment already exists: $VENV_NAME"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source $VENV_NAME/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
uv pip install --upgrade pip

# Install the project in development mode
echo "📦 Installing project dependencies..."
uv pip install -e ".[dev]"

# Check if .env file exists, create template if not
if [ ! -f ".env" ]; then
    echo "📝 Creating .env template file..."
    cat > .env << EOF
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB=ragdb

# Jina AI Configuration (get your API key from https://jina.ai/)
JINA_API_KEY=your_jina_api_key_here

# Embedding Configuration
EMBED_MODEL=jina-embeddings-v3
EMBED_TASK=text-matching

# Celery Configuration
BROKER_URL=redis://localhost:6379/0
RESULT_BACKEND=redis://localhost:6379/1

# Processing Configuration
CHUNK_MAX_TOKENS=512
LOG_LEVEL=INFO
EOF
    echo "⚠️  Please edit .env file and add your Jina API key!"
else
    echo "✅ .env file already exists"
fi

# Make scripts executable
echo "🔨 Making scripts executable..."
chmod +x start_mongo.sh
chmod +x scripts/*.sh

# Start services
echo "🚀 Starting required services..."

# Start MongoDB
echo "📊 Starting MongoDB..."
./start_mongo.sh

# Start Redis
echo "📮 Starting Redis..."
./scripts/redis_up.sh

# Final instructions
echo ""
echo "🎉 Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your Jina API key"
echo "2. Activate virtual environment: source $VENV_NAME/bin/activate"
echo "3. Start Celery workers: ./scripts/run_workers.sh"
echo "4. Ingest test data: rag-ingest ingest test_data/"
echo ""
echo "🔧 Available commands:"
echo "  rag-ingest scan test_data/        # Preview files to be ingested"
echo "  rag-ingest ingest test_data/      # Ingest all PDF files"
echo "  rag-ingest search 'query text'   # Search ingested documents"
echo ""
echo "🛑 To stop services:"
echo "  docker stop mongo-rag22 redis-rag"
echo ""
echo "✨ Happy coding!"
