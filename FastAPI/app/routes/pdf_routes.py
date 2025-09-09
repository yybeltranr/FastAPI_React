from fastapi import APIRouter, UploadFile, File
import shutil, os
from app.controllers.pdf_controller import procesar_pdf

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/procesar")
async def procesar_pdf_route(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    resultado = procesar_pdf(file_path)
    return resultado