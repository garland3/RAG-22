#!/bin/bash

# Run Celery workers for RAG ingestion

celery -A workers.tasks worker --loglevel=info