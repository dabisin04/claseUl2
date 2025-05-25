import time
import mysql.connector
import os
from mysql.connector import Error

def wait_for_db():
    max_retries = 30
    retry_interval = 2
    
    for attempt in range(max_retries):
        try:
            print("⏳ Esperando que MySQL esté disponible en db:3306...")
            connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'db'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', 'root'),
                database=os.getenv('DB_NAME', 'the_library')
            )
            
            if connection.is_connected():
                print("✅ MySQL está disponible, iniciando app.")
                connection.close()
                return True
                
        except Error as e:
            print(f"❌ Base de datos no disponible aún, reintentando en {retry_interval} segundos...")
            time.sleep(retry_interval)
            
    print("❌ No se pudo conectar a la base de datos después de varios intentos")
    return False

if __name__ == "__main__":
    wait_for_db() 