"""
main.py - Punto de entrada de la aplicación FastAPI.
"""
from app.routes import pdf_routes
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="PDF Extractor API")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas
app.include_router(pdf_routes.router, prefix="/pdf", tags=["PDF y Excel"])


# Endpoint raíz
@app.get("/")
def root():
    return {"message": "API PDF Extractor corriendo"}