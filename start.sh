#!/bin/bash

# Esperar a que la base de datos esté disponible
python db_wait.py

# Iniciar FastAPI en segundo plano
cd app_fastapi && uvicorn main:app --host 0.0.0.0 --port 5002 --reload &

# Iniciar Flask
cd app && python app.py --port 5001 