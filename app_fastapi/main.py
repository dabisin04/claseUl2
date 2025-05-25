from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.db import client, db
import uvicorn

app = FastAPI(
    title="Books API NoSQL",
    description="API para gestión de libros usando FastAPI y MongoDB",
    version="1.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexión a MongoDB
@app.on_event("startup")
async def startup_db_client():
    app.mongodb = db

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Importar routers
from api.book_api import router as book_router
from api.chapters_api import router as chapter_router
from api.comment_api import router as comment_router
from api.rating_api import router as rating_router
from api.user_api import router as user_router
from api.favorite_api import router as favorite_router
from api.reports_api import router as reports_router

# Incluir routers
app.include_router(user_router, prefix="/api", tags=["users"])
app.include_router(book_router, prefix="/api", tags=["books"])
app.include_router(chapter_router, prefix="/api", tags=["chapters"])
app.include_router(comment_router, prefix="/api", tags=["comments"])
app.include_router(rating_router, prefix="/api", tags=["ratings"])
app.include_router(favorite_router, prefix="/api", tags=["favorites"])
app.include_router(reports_router, prefix="/api", tags=["reports"])

@app.get("/")
async def root():
    return {"message": "✅ API de libros NoSQL funcionando correctamente"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5002, reload=True) 