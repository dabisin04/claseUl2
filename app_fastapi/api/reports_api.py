from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from models.reports import Report, ReportCreate
from models.report_alerts import ReportAlert, ReportAlertCreate
from models.user_strikes import UserStrike, UserStrikeCreate
from datetime import datetime
from config.db import reports, users, books, comments, report_alerts, user_strikes
import os
import uuid
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

router = APIRouter()


def _is_valid_uuid(val: str) -> bool:
    if not val or not isinstance(val, str):
        return False
    try:
        uuid.UUID(val)
        return True
    except (ValueError, AttributeError, TypeError):
        return False

def convert_flask_report(flask_report: dict) -> dict:
    logger.info(f"Convirtiendo reporte de Flask para objetivo {flask_report.get('target_id')}")
    id_value = flask_report.get("id")
    if not _is_valid_uuid(id_value):
        id_value = str(uuid.uuid4())
        logger.info(f"ID inválido o faltante, generando nuevo UUID: {id_value}")

    return {
        "_id": id_value,
        "reporter_id": flask_report["reporter_id"],
        "target_id": flask_report["target_id"],
        "target_type": flask_report["target_type"],
        "reason": flask_report["reason"],
        "status": flask_report.get("status", "pending"),
        "admin_id": flask_report.get("admin_id"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "timestamp": flask_report.get("timestamp") or datetime.utcnow(),
        "resolved_at": flask_report.get("resolved_at")
    }

def convert_flask_alert(flask_alert: dict) -> dict:
    logger.info(f"Convirtiendo alerta de Flask para libro {flask_alert.get('book_id')}")
    id_value = flask_alert.get("id")
    if not _is_valid_uuid(id_value):
        id_value = str(uuid.uuid4())
    return {
        "_id": id_value,
        "book_id": flask_alert["book_id"],
        "report_reason": flask_alert["report_reason"],
        "status": flask_alert.get("status", "alert"),
        "created_at": flask_alert.get("created_at", datetime.utcnow())
    }

def convert_flask_strike(flask_strike: dict) -> dict:
    logger.info(f"Convirtiendo strike de Flask para usuario {flask_strike.get('user_id')}")
    id_value = flask_strike.get("id")
    if not _is_valid_uuid(id_value):
        id_value = str(uuid.uuid4())
    return {
        "_id": id_value,
        "user_id": flask_strike["user_id"],
        "reason": flask_strike["reason"],
        "strike_count": flask_strike.get("strike_count", 1),
        "is_active": flask_strike.get("is_active", True),
        "created_at": flask_strike.get("created_at", datetime.utcnow()),
        "updated_at": flask_strike.get("updated_at", datetime.utcnow())
    }

def to_response(doc):
    if not doc:
        return None
    return doc  # Mantén "_id" sin cambios

@router.post("/addReport", response_model=Report)
async def add_report(report: ReportCreate):
    try:
        reporter = users.find_one({"_id": str(report.reporter_id)})
        if not reporter:
            raise HTTPException(status_code=404, detail="El usuario que reporta no existe")

        target_map = {"book": books, "user": users, "comment": comments}
        if report.target_type not in target_map:
            raise HTTPException(status_code=400, detail="Tipo de objetivo inválido")

        target = target_map[report.target_type].find_one({"_id": str(report.target_id)})
        if not target:
            raise HTTPException(status_code=404, detail=f"{report.target_type.capitalize()} no encontrado")

        if getattr(report, "from_flask", False):
            report_data = convert_flask_report(report.model_dump())
        else:
            report_data = report.model_dump()
            report_data["_id"] = report.id or str(uuid.uuid4())
            report_data.update({"created_at": datetime.utcnow(), "updated_at": datetime.utcnow()})

        result = reports.insert_one(report_data)
        logger.debug(f"🧾 Documento final a insertar: {report_data}")

        total = reports.count_documents({"target_id": str(report.target_id), "target_type": report.target_type})

        if report.target_type == "book" and total >= 5:
            if not report_alerts.find_one({"book_id": str(report.target_id), "status": "alert"}):
                alert = ReportAlertCreate(book_id=str(report.target_id), report_reason="Acumulación de reportes")
                alert_data = convert_flask_alert(alert.model_dump())
                report_alerts.insert_one(alert_data)
                books.update_one({"_id": str(report.target_id)}, {"$set": {"status": "alert"}})

        if report.target_type == "comment" and report.reason.lower() in ["ofensivo", "acoso", "lenguaje inapropiado"]:
            comment = comments.find_one({"_id": str(report.target_id)})
            if comment:
                strike = UserStrikeCreate(
                    user_id=comment["user_id"],
                    reason=report.reason,
                    from_flask=report.from_flask if hasattr(report, "from_flask") else False,
                    id=report.id if hasattr(report, "id") else None
                )
                strike_data = convert_flask_strike(strike.model_dump())
                user_strikes.insert_one(strike_data)

        new_report = reports.find_one({"_id": result.inserted_id})
        if not new_report:
            raise HTTPException(status_code=500, detail="Error al recuperar el reporte insertado")

        return Report.model_validate(to_response(new_report))
    except Exception as e:
        logger.error(f"Error al procesar el reporte: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports", response_model=List[Report])
async def get_all_reports():
    return [Report.model_validate(to_response(r)) for r in reports.find()]

@router.get("/reportsByTarget/{target_id}", response_model=List[Report])
async def get_reports_by_target(target_id: str):
    return [Report.model_validate(to_response(r)) for r in reports.find({"target_id": target_id})]

@router.put("/updateReportStatus/{report_id}", response_model=Report)
async def update_report_status(report_id: str, status: str, admin_id: Optional[str] = None):
    update_data = {"status": status, "updated_at": datetime.utcnow()}
    if admin_id:
        update_data["admin_id"] = str(admin_id)

    reports.update_one({"_id": report_id}, {"$set": update_data})
    updated = reports.find_one({"_id": report_id})
    if not updated:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return Report.model_validate(to_response(updated))

@router.post("/addStrike", response_model=UserStrike)
async def add_strike(strike: UserStrikeCreate):
    strike_data = convert_flask_strike(strike.model_dump())
    result = user_strikes.insert_one(strike_data)
    return UserStrike.model_validate(to_response(user_strikes.find_one({"_id": result.inserted_id})))

@router.get("/strikesByUser/{user_id}", response_model=List[UserStrike])
async def get_strikes_by_user(user_id: str):
    return [UserStrike.model_validate(to_response(s)) for s in user_strikes.find({"user_id": user_id})]

@router.post("/addAlert", response_model=ReportAlert)
async def add_alert(alert: ReportAlertCreate):
    alert_data = convert_flask_alert(alert.model_dump())
    result = report_alerts.insert_one(alert_data)
    return ReportAlert.model_validate(to_response(report_alerts.find_one({"_id": result.inserted_id})))

@router.get("/alertsByBook/{book_id}", response_model=List[ReportAlert])
async def get_alerts_by_book(book_id: str):
    return [ReportAlert.model_validate(to_response(a)) for a in report_alerts.find({"book_id": book_id})]

@router.put("/resolveAlert/{alert_id}", response_model=ReportAlert)
async def resolve_alert(alert_id: str, status: str = Query("resolved")):
    report_alerts.update_one({"_id": alert_id}, {"$set": {"status": status}})
    if status == "resolved":
        alert = report_alerts.find_one({"_id": alert_id})
        if alert:
            books.update_one({"_id": alert["book_id"]}, {"$set": {"status": "active"}})
    updated = report_alerts.find_one({"_id": alert_id})
    if not updated:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return ReportAlert.model_validate(to_response(updated))
