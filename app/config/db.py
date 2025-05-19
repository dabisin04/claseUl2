import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)

# Variables de entorno
user = os.getenv('DB_USER', 'root')
password = os.getenv('DB_PASSWORD', 'root')
direc = os.getenv('DB_HOST', 'localhost')
namebd = os.getenv('DB_NAME', 'the_library')  # CAMBIADO aquí el nombre de la BD

# Configuración SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{user}:{password}@{direc}/{namebd}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "Movil2"

# Inicialización de extensiones
db = SQLAlchemy(app)
ma = Marshmallow(app)
