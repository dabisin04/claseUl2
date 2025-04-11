import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)

# Configuración con datos de PythonAnywhere
user = os.getenv('DB_USER', 'dabisin04')
password = os.getenv('DB_PASSWORD', 'DabisinCampo159.')
direc = os.getenv('DB_HOST', 'dabisin04.mysql.pythonanywhere-services.com')
namebd = os.getenv('DB_NAME', 'dabisin04$default')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{user}:{password}@{direc}/{namebd}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "Movil2"

db = SQLAlchemy(app)
ma = Marshmallow(app)
