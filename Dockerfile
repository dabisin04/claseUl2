FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["bash", "-c", "python db_wait.py && python app.py"]
