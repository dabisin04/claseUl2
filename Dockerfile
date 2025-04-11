FROM python:3.10

WORKDIR /app  

# Copiar todos los archivos del proyecto a /app en el contenedor
COPY . /app/

# Instalar las dependencias desde el requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto en el que Flask estará corriendo
EXPOSE 5000

# Ejecutar el archivo app.py que está en la raíz del directorio
CMD ["python", "app.py"]
