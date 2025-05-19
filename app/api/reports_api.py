from flask import Blueprint, request, jsonify
from config.db import db
from models.reports import Report, ReportSchema
from models.user_strikes import UserStrike, UserStrikeSchema
from models.report_alerts import ReportAlert, ReportAlertSchema
from functools import wraps
import os

API_KEY = os.environ.get("API_KEY")

ruta_reportes = Blueprint("route_reports", __name__)
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

# ---------- REPORTES ----------

@ruta_reportes.route("/addReport", methods=["POST"])
@require_api_key()
def add_report():
    data = request.json
    new_report = Report(
        reporter_id=data["reporter_id"],
        target_id=data["target_id"],
        target_type=data["target_type"],
        reason=data["reason"]
    )
    db.session.add(new_report)
    db.session.commit()
    return report_schema.jsonify(new_report), 201

@ruta_reportes.route("/reports", methods=["GET"])
@require_api_key()
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
    strikes = UserStrike.query.filter_by(user_id=user_id).all()
    return strikes_schema.jsonify(strikes)

# ---------- ALERTAS ----------

@ruta_reportes.route("/addAlert", methods=["POST"])
@require_api_key()
def add_alert():
    data = request.json
    new_alert = ReportAlert(
        target_id=data["target_id"],
        target_type=data["target_type"],
        status="alert",
        reason=data.get("reason", "")
    )
    db.session.add(new_alert)
    db.session.commit()
    return alert_schema.jsonify(new_alert), 201

@ruta_reportes.route("/alertsByType/<string:target_type>", methods=["GET"])
@require_api_key()
def get_alerts_by_type(target_type):
    alerts = ReportAlert.query.filter_by(target_type=target_type).all()
    return alerts_schema.jsonify(alerts)

@ruta_reportes.route("/resolveAlert/<string:alert_id>", methods=["PUT"])
@require_api_key()
def resolve_alert(alert_id):
    data = request.json
    alert = ReportAlert.query.get(alert_id)
    if not alert:
        return jsonify({"error": "Alerta no encontrada"}), 404
    alert.status = data.get("status", "resolved")
    db.session.commit()
    return alert_schema.jsonify(alert)
