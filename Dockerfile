FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000 5001

# Crear un script de inicio usando un archivo temporal
RUN echo '#!/bin/bash' > /tmp/start.sh && \
    echo 'python db_wait.py' >> /tmp/start.sh && \
    echo 'uvicorn main:app --host 0.0.0.0 --port 5000 --reload &' >> /tmp/start.sh && \
    echo 'python app/app.py --port 5001' >> /tmp/start.sh && \
    chmod +x /tmp/start.sh

CMD ["/bin/bash", "/tmp/start.sh"]
