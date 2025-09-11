from app.services.pdf_service import extraer_texto, extraer_tablas, encontrar_maximo_movimiento
import os

def procesar_pdf(file_path: str, banco: str):
    info_textual = extraer_texto(file_path)
    info_tablas = extraer_tablas(file_path)
    max_movimiento = encontrar_maximo_movimiento(file_path, banco)

    return {
        "banco": banco, 
        "texto": info_textual, 
        "tablas": info_tablas, 
        "max_movimiento": max_movimiento
    }