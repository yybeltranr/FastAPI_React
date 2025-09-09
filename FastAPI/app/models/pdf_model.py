from pydantic import BaseModel
from typing import Dict

class PDFTextResult(BaseModel):
    CUENTA: str
    NUMERO: str

class PDFTableResult(BaseModel):
    SALDO_INICIAL: str
    MOVIMIENTO_DE_INGRESOS: str
    MOVIMIENTO_DE_EGRESOS: str
    SALDO_FINAL: str

class PDFResult(BaseModel):
    texto: Dict[str, str]
    tablas: Dict[str, str]
