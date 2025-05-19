import time
import pymysql
import os

host = os.getenv("DB_HOST", "localhost")
port = int(os.getenv("DB_PORT", "3306"))
user = os.getenv("DB_USER", "root")
password = os.getenv("DB_PASSWORD", "root")
database = os.getenv("DB_NAME", "the_library")

print(f"⏳ Esperando que MySQL esté disponible en {host}:{port}...")

while True:
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database)
        conn.close()
        print("✅ MySQL está disponible, iniciando app.")
        break
    except Exception as e:
        print("❌ Base de datos no disponible aún, reintentando en 2 segundos...")
        time.sleep(2)
