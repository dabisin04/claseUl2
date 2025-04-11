from flask import Flask, Blueprint, request, redirect, render_template, jsonify
from config.db import app, db, ma

from models.TaksModel import Taks, TaksSchema

ruta_tak = Blueprint("route_task", __name__)

tarea_schema = TaksSchema()
tareas_schemea = TaksSchema(many=True)


@ruta_tak.route("/taks")
def alltak():
    resultAll = Taks.query.all()
    respo = tareas_schemea.dump(resultAll)
    return jsonify(respo)


@ruta_tak.route("/registrarTarea", methods=["POST"])
def registrarTarea():
    nametak = request.json["nametak"]
    idUser_fk = request.json["idUser_fk"]
    idCategory_fk = request.json["idCategory_fk"]
    newtak = Taks(nametak, idUser_fk, idCategory_fk)
    db.session.add(newtak)
    db.session.commit()
    return "Guardado"


@ruta_tak.route("eliminarTarea", methods=["POST"])
def eliminarTarea():
    id = request.json["id"]
    tarea = Taks.query.get(id)
    db.session.delete(tarea)
    db.session.commit()
    return jsonify(tarea_schema.dump(tarea))
