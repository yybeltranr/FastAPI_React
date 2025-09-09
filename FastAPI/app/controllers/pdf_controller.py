from app.services.pdf_service import extraer_texto, extraer_tablas
import os

def procesar_pdf(file_path: str):
    info_textual = extraer_texto(file_path)
    info_tablas = extraer_tablas(file_path)

    return {"texto": info_textual, "tablas": info_tablas}