#!/bin/bash

# Start Redis in the background
redis-server --daemonize yes

# Wait for Redis to be ready
sleep 1

# Start FastAPI/Uvicorn
# Make sure "main:app" matches your file name (main.py) and FastAPI instance (app = FastAPI())
exec uvicorn main:app --host 0.0.0.0 --port 8000
