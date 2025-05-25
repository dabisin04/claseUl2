from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Optional
from models.reports import Report, ReportCreate
from models.report_alerts import ReportAlert, ReportAlertCreate
from models.user_strikes import UserStrike, UserStrikeCreate
from datetime import datetime, timedelta
from bson import ObjectId
from config.db import reports, users, books, comments, report_alerts, user_strikes

router = APIRouter()

# 🔹 Agregar reporte
@router.post("/addReport", response_model=Report)
async def add_report(report: ReportCreate):
    reporter = users.find_one({"_id": ObjectId(report.reporter_id)})
    if not reporter:
        raise HTTPException(status_code=404, detail="El usuario que reporta no existe")

    # Validar el objetivo del reporte
    target_collections = {"book": books, "user": users, "comment": comments}
    if report.target_type not in target_collections:
        raise HTTPException(status_code=400, detail="Tipo de objetivo inválido")

    target = target_collections[report.target_type].find_one({"_id": ObjectId(report.target_id)})
    if not target:
        raise HTTPException(status_code=404, detail=f"{report.target_type.capitalize()} no encontrado")

    report_data = report.model_dump()
    report_data.update({
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    result = reports.insert_one(report_data)
    total_reports = reports.count_documents({
        "target_id": report.target_id,
        "target_type": report.target_type
    })

    # 🚨 ALERTAS: Libros con 5+ reportes
    if report.target_type == "book" and total_reports >= 5:
        if not report_alerts.find_one({"book_id": report.target_id, "status": "alert"}):
            alert = ReportAlertCreate(
                book_id=report.target_id,
                report_reason="Acumulación de reportes",
                status="alert"
            )
            report_alerts.insert_one({
                **alert.model_dump(),
                "created_at": datetime.utcnow()
            })
            books.update_one({"_id": ObjectId(report.target_id)}, {"$set": {"status": "alert"}})

    # ❗ STRIKES por comentarios ofensivos
    if report.target_type == "comment" and report.reason.lower() in ["ofensivo", "acoso", "lenguaje inapropiado"]:
        comment = comments.find_one({"_id": ObjectId(report.target_id)})
        if comment:
            strike = UserStrikeCreate(user_id=comment["user_id"], reason=report.reason)
            user_strikes.insert_one({
                **strike.model_dump(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })

    # 🔤 NOMBRE INAPROPIADO
    if report.target_type == "user" and report.reason.lower() == "nombre inapropiado":
        name_reports = reports.count_documents({
            "target_id": report.target_id,
            "target_type": "user",
            "reason": "nombre inapropiado"
        })
        if name_reports >= 3:
            users.update_one(
                {"_id": ObjectId(report.target_id)},
                {"$set": {
                    "status": "rename_required",
                    "name_change_deadline": (datetime.utcnow() + timedelta(days=7)).isoformat()
                }}
            )

    new_report = reports.find_one({"_id": result.inserted_id})
    new_report["id"] = str(new_report["_id"])
    return Report.model_validate(new_report)

# 🔹 Obtener todos los reportes
@router.get("/reports", response_model=List[Report])
async def get_all_reports():
    return [Report.model_validate({**r, "id": str(r["_id"])}) for r in reports.find()]

# 🔹 Obtener reportes por objetivo
@router.get("/reportsByTarget/{target_id}", response_model=List[Report])
async def get_reports_by_target(target_id: str):
    return [Report.model_validate({**r, "id": str(r["_id"])}) for r in reports.find({"target_id": target_id})]

# 🔹 Actualizar estado de un reporte
@router.put("/updateReportStatus/{report_id}", response_model=Report)
async def update_report_status(report_id: str, status: str, admin_id: Optional[str] = None):
    update_data = {
        "status": status,
        "updated_at": datetime.utcnow()
    }
    if admin_id:
        update_data["admin_id"] = admin_id

    reports.update_one({"_id": ObjectId(report_id)}, {"$set": update_data})
    updated = reports.find_one({"_id": ObjectId(report_id)})
    if not updated:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    updated["id"] = str(updated["_id"])
    return Report.model_validate(updated)

# 🔹 Agregar strike manual
@router.post("/addStrike", response_model=UserStrike)
async def add_strike(strike: UserStrikeCreate):
    data = strike.model_dump()
    data["created_at"] = datetime.utcnow()
    data["updated_at"] = datetime.utcnow()
    result = user_strikes.insert_one(data)
    inserted = user_strikes.find_one({"_id": result.inserted_id})
    inserted["id"] = str(inserted["_id"])
    return UserStrike.model_validate(inserted)

# 🔹 Obtener strikes por usuario
@router.get("/strikesByUser/{user_id}", response_model=List[UserStrike])
async def get_strikes_by_user(user_id: str):
    return [UserStrike.model_validate({**s, "id": str(s["_id"])}) for s in user_strikes.find({"user_id": user_id})]

# 🔹 Agregar alerta manual
@router.post("/addAlert", response_model=ReportAlert)
async def add_alert(alert: ReportAlertCreate):
    data = alert.model_dump()
    data["created_at"] = datetime.utcnow()
    result = report_alerts.insert_one(data)
    inserted = report_alerts.find_one({"_id": result.inserted_id})
    inserted["id"] = str(inserted["_id"])
    return ReportAlert.model_validate(inserted)

# 🔹 Obtener alertas por libro
@router.get("/alertsByBook/{book_id}", response_model=List[ReportAlert])
async def get_alerts_by_book(book_id: str):
    return [ReportAlert.model_validate({**a, "id": str(a["_id"])}) for a in report_alerts.find({"book_id": book_id})]

# 🔹 Resolver alerta
@router.put("/resolveAlert/{alert_id}", response_model=ReportAlert)
async def resolve_alert(alert_id: str, status: str = Query("resolved")):
    report_alerts.update_one(
        {"_id": ObjectId(alert_id)},
        {"$set": {"status": status}}
    )

    if status == "resolved":
        alert = report_alerts.find_one({"_id": ObjectId(alert_id)})
        if alert:
            books.update_one(
                {"_id": ObjectId(alert["book_id"])},
                {"$set": {"status": "active"}}
            )

    updated = report_alerts.find_one({"_id": ObjectId(alert_id)})
    if not updated:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    updated["id"] = str(updated["_id"])
    return ReportAlert.model_validate(updated)
