from flask import Blueprint, request, jsonify
from config.db import db
from models.reports import Report, ReportSchema
from models.user_strikes import UserStrike, UserStrikeSchema
from models.report_alerts import ReportAlert, ReportAlertSchema
from models.book import Book
from models.user import User
from models.comment import Comment
from functools import wraps
from datetime import datetime, timedelta
import os

API_KEY = os.environ.get("API_KEY")

ruta_reportes = Blueprint("ruta_reports", __name__)
report_schema = ReportSchema()
reports_schema = ReportSchema(many=True)
strike_schema = UserStrikeSchema()
strikes_schema = UserStrikeSchema(many=True)
alert_schema = ReportAlertSchema()
alerts_schema = ReportAlertSchema(many=True)

def require_api_key():
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = request.headers.get("X-API-KEY")
            if key != API_KEY:
                return jsonify({"error": "No autorizado"}), 401
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ---------- AGREGAR REPORTE ----------

@ruta_reportes.route("/addReport", methods=["POST"])
def add_report():
    data = request.json
    
    # Validar que el usuario que reporta existe
    reporter = User.query.get(data["reporter_id"])
    if not reporter:
        return jsonify({"error": "El usuario que reporta no existe"}), 404
    
    # Validar que el objetivo del reporte existe según su tipo
    if data["target_type"] == "book":
        target = Book.query.get(data["target_id"])
        if not target:
            return jsonify({"error": "El libro reportado no existe"}), 404
    elif data["target_type"] == "user":
        target = User.query.get(data["target_id"])
        if not target:
            return jsonify({"error": "El usuario reportado no existe"}), 404
    elif data["target_type"] == "comment":
        target = Comment.query.get(data["target_id"])
        if not target:
            return jsonify({"error": "El comentario reportado no existe"}), 404
    
    new_report = Report(
        reporter_id=data["reporter_id"],
        target_id=data["target_id"],
        target_type=data["target_type"],
        reason=data["reason"]
    )
    db.session.add(new_report)
    db.session.commit()

    # Verificar acumulación de reportes
    total_reports = Report.query.filter_by(
        target_id=data["target_id"],
        target_type=data["target_type"]
    ).count()

    # ─── ALERTA POR LIBROS ───
    if data["target_type"] == "book" and total_reports >= 5:
        existing_alert = ReportAlert.query.filter_by(
            book_id=data["target_id"], status="alert"
        ).first()
        if not existing_alert:
            alert = ReportAlert(
                book_id=data["target_id"],
                report_reason="Acumulación de reportes",
                status="alert",
                created_at=datetime.utcnow().isoformat()
            )
            db.session.add(alert)

            libro = Book.query.get(data["target_id"])
            if libro:
                libro.status = "alert"

    # ─── STRIKES POR COMENTARIOS ───
    if data["target_type"] == "comment" and data["reason"].lower() in ["ofensivo", "acoso", "lenguaje inapropiado"]:
        comment = Comment.query.get(data["target_id"])
        if comment:
            strike = UserStrike(user_id=comment.user_id, reason=data["reason"])
            db.session.add(strike)

    # ─── REVISIÓN DE NOMBRE INAPROPIADO ───
    if data["target_type"] == "user" and data["reason"].lower() == "nombre inapropiado":
        name_reports = Report.query.filter_by(
            target_id=data["target_id"],
            target_type="user",
            reason="nombre inapropiado"
        ).count()

        if name_reports >= 3:
            usuario = User.query.get(data["target_id"])
            if usuario and usuario.status != "rename_required":
                usuario.status = "rename_required"
                if hasattr(usuario, 'name_change_deadline'):
                    usuario.name_change_deadline = (datetime.utcnow() + timedelta(days=7)).isoformat()

    db.session.commit()
    return report_schema.jsonify(new_report), 201

# ---------- OBTENER REPORTES ----------

@ruta_reportes.route("/reports", methods=["GET"])
def get_all_reports():
    reports = Report.query.all()
    return reports_schema.jsonify(reports)

@ruta_reportes.route("/reportsByTarget/<string:target_id>", methods=["GET"])
@require_api_key()
def get_reports_by_target(target_id):
    reports = Report.query.filter_by(target_id=target_id).all()
    return reports_schema.jsonify(reports)

@ruta_reportes.route("/updateReportStatus/<string:report_id>", methods=["PUT"])
@require_api_key()
def update_report_status(report_id):
    data = request.json
    report = Report.query.get(report_id)
    if not report:
        return jsonify({"error": "Reporte no encontrado"}), 404
    report.status = data.get("status", "reviewed")
    report.admin_id = data.get("admin_id")
    db.session.commit()
    return report_schema.jsonify(report)

# ---------- STRIKES ----------

@ruta_reportes.route("/addStrike", methods=["POST"])
@require_api_key()
def add_strike():
    data = request.json
    # Verificar que el usuario existe
    user = User.query.get(data["user_id"])
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    new_strike = UserStrike(
        user_id=data["user_id"],
        reason=data["reason"]
    )
    db.session.add(new_strike)
    db.session.commit()
    return strike_schema.jsonify(new_strike), 201

@ruta_reportes.route("/strikesByUser/<string:user_id>", methods=["GET"])
@require_api_key()
def get_strikes_by_user(user_id):
    # Verificar que el usuario existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    strikes = UserStrike.query.filter_by(user_id=user_id).all()
    return strikes_schema.jsonify(strikes)

# ---------- ALERTAS ----------

@ruta_reportes.route("/addAlert", methods=["POST"])
@require_api_key()
def add_alert():
    data = request.json
    # Verificar que el libro existe
    book = Book.query.get(data["book_id"])
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    new_alert = ReportAlert(
        book_id=data["book_id"],
        report_reason=data.get("report_reason", ""),
        status="alert",
        created_at=datetime.utcnow().isoformat()
    )
    db.session.add(new_alert)
    db.session.commit()
    return alert_schema.jsonify(new_alert), 201

@ruta_reportes.route("/alertsByBook/<string:book_id>", methods=["GET"])
@require_api_key()
def get_alerts_by_book(book_id):
    # Verificar que el libro existe
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    alerts = ReportAlert.query.filter_by(book_id=book_id).all()
    return alerts_schema.jsonify(alerts)

@ruta_reportes.route("/resolveAlert/<string:alert_id>", methods=["PUT"])
@require_api_key()
def resolve_alert(alert_id):
    data = request.json
    alert = ReportAlert.query.get(alert_id)
    if not alert:
        return jsonify({"error": "Alerta no encontrada"}), 404
    
    alert.status = data.get("status", "resolved")
    
    # Actualizar el estado del libro si la alerta se resuelve
    if alert.status == "resolved":
        libro = Book.query.get(alert.book_id)
        if libro and libro.status == "alert":
            libro.status = "active"
    
    db.session.commit()
    return alert_schema.jsonify(alert)
