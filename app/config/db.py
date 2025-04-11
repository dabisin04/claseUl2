import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)

# Usar las variables de entorno para la configuración
user = os.getenv('DB_USER', 'root')  # Valor predeterminado 'root' si no está configurado
password = os.getenv('DB_PASSWORD', 'root')
direc = os.getenv('DB_HOST', 'localhost')  # Nombre del servicio en Docker Compose
namebd = os.getenv('DB_NAME', 'tasksul')  # Nombre de la base de datos

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{user}:{password}@{direc}/{namebd}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "Movil2"

db = SQLAlchemy(app)
ma = Marshmallow(app)
