from fastapi import APIRouter, UploadFile, File, Form
import shutil, os

from fastapi.responses import FileResponse
from app.services.pdf_service import exportar_a_excel
from app.controllers.pdf_controller import procesar_pdf

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/procesar")
async def procesar_pdf_route(file: UploadFile = File(...), banco: str = Form(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    resultado = procesar_pdf(file_path, banco)
    return resultado

@router.post("/exportar-excel")
async def exportar_excel_endpoint(data: dict):
    plantilla_path = os.path.join(os.path.dirname(__file__), "../templates_excel/PlantillaSIVICOF.xlsx")
    nombre_archivo = "Informe_SIVICOF.xlsx"

    OUTPUT_DIR = "outputs"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, nombre_archivo)

    resultados = data.get("resultados", {})  # resultados por banco
    valores_frontend = data.get("valores_frontend", {})  # valores del frontend
    fecha_conciliacion = data.get("fechaConciliacion", None)
    responsable_cargo = data.get("responsableCargo", "")
    poliza = data.get("poliza", "")

    exportar_a_excel(
        resultados=resultados,
        valores_frontend=valores_frontend,
        fecha_conciliacion=fecha_conciliacion,
        responsable_cargo=responsable_cargo,
        poliza=poliza,
        plantilla_path=plantilla_path,
        output_path=output_path
    )

    return FileResponse(
        path=output_path,
        filename=nombre_archivo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
