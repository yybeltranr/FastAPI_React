"""
main.py - Punto de entrada de la aplicación FastAPI.
"""
from app.routes import pdf_routes
from fastapi import FastAPI

app = FastAPI(title="PDF Extractor API")

# Registrar rutas
app.include_router(pdf_routes.router, prefix="/pdf", tags=["PDF"])

# Endpoint raíz
@app.get("/")
def root():
    return {"message": "API PDF Extractor corriendo"}