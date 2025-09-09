import re, os
from pypdf import PdfReader
import pdfplumber
import pandas as pd
from openpyxl import load_workbook

def extraer_texto(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        all_text = ""
        for page in reader.pages:
            txt = page.extract_text()
            if txt:
                all_text += txt + "\n"

        # Limpiar líneas
        lines = [ln.strip() for ln in all_text.splitlines() if ln.strip()]
        whole_text = "\n".join(lines)

        # DEBUG: imprimir línea por línea
        #print("\n===== EXTRACCIÓN LÍNEA A LÍNEA =====")
        #for i, ln in enumerate(lines, 1):
        #    print(f"[LÍNEA {i}] {ln}")


        # Extraer posibles números de cuenta del nombre del archivo
        filename = os.path.basename(pdf_path)
        # Buscar secuencias de 8 a 20 dígitos en el nombre (cuentas largas aunque terminen en _ o -)
        m_cuenta = re.findall(r"(\d{9,20})(?=[^\d]|$)", filename)
        # Buscar también casos tipo "No.9670" en el nombre
        m_cuenta_short = re.findall(r"No\.?\s*([0-9\-]{4,10})", filename, re.IGNORECASE)

        # Elegir primero cuentas largas, si no hay usar cortas
        if m_cuenta:
            numero_en_nombre = m_cuenta[0]
        elif m_cuenta_short:
            # limpiar por si trae guiones o puntos
            numero_en_nombre = re.sub(r"[^\d]", "", m_cuenta_short[0])
        else:
            numero_en_nombre = None

        # Buscar últimos 4 dígitos
        m4 = re.findall(r"(\d{4})", filename)
        ultimos4 = m4[0] if m4 else None

        # Patrones, el orden importa
        patterns = {
            "CUENTA": [
                r"CUENTA(?:\s+DE)?\s+(AHORROS|CORRIENTE)"
            ],
            "NÚMERO": [
                r"No\.\s+Inversión\s*\n\s*([\d\s]{6,40})", # FiduOccidente
                r"Cuenta\s*no\.?\s*\n\s*([\d\-]{6,30})", #Cuenta no. minúsculas con salto
                r"CUENTA\s+DE\s+AHORROS\s*\n\s*([\d\s]{6,40})", # Davivienda (con espacios y salto)
                r"CUENTA\s+DE\s+AHORROS\s*([\d\s]{6,40})", # Davivienda (con espacios, sin salto)
                r"CUENTA\s+No\.?\s*\n\s*([\d\s\-]{6,30})", # CUENTA No. con salto
                r"CUENTA\s+No\.?\s*([\d\-]+)",         # CUENTA No. inline con separadores -
                r"CUENTA\s+No\.?\s*(\d+)",            # CUENTA No. inline
                r"No\.?\s+([\d\-]{6,30})",
                r"^\d{10,20}$",                       # puro dígito
                r"No(?!\.)\s*(\d+)",                  # No 1234
                r"NÚMERO\s*([0-9]+)",                 # genérico
            ]
        }

        info_textual = {}
        for key, regex_list in patterns.items():
            val = None

            for ln in lines:
                for pattern in regex_list:
                    m = re.search(pattern, ln, re.IGNORECASE)
                    if m:
                        val = m.group(1) if m.lastindex else m.group(0)
                        break
                if val:
                    break

            if not val:
                for pattern in regex_list:
                    m = re.search(pattern, whole_text, re.IGNORECASE)
                    if m:
                        val = m.group(1) if m.lastindex else m.group(0)
                        break

            # Postproceso
            if key == "NÚMERO":
                if val:
                    limpio = re.sub(r"[^\d]", "", val)  # quitar guiones, espacios
                    if ultimos4 and limpio.endswith(ultimos4) and 8 <= len(limpio) <= 20:
                        info_textual[key] = limpio
                    else:
                        if numero_en_nombre and limpio.endswith(numero_en_nombre):
                            info_textual[key] = limpio
                        elif numero_en_nombre:
                            info_textual[key] = numero_en_nombre
                        else:
                            info_textual[key] = "No encontrado"
                else:
                    if numero_en_nombre:
                        info_textual[key] = numero_en_nombre
                    else:
                        info_textual[key] = "No encontrado"
            else:
                info_textual[key] = val.strip() if val else "No encontrado"

        return info_textual

        if info_textual["CUENTA"] == "No encontrado" and info_textual["NÚMERO"] == "No encontrado":
            # Caso especial Davivienda
            davivienda_info = extraer_davivienda(lines, ultimos4)
            info_textual.update(davivienda_info)

    except Exception as e:
        print(f"[ERROR] {e}")
        return {k: "PDF no se puede leer" for k in ["CUENTA", "NÚMERO"]}


def extraer_davivienda(lines, ultimos4):
    cuenta = "No encontrado"
    numero = "No encontrado"

    for i, ln in enumerate(lines):
        if re.search(r"CUENTA\s+DE\s+AHORROS", ln, re.IGNORECASE):
            if i + 1 < len(lines):
                candidato = lines[i+1].strip()
                limpio = re.sub(r"[^\d]", "", candidato)
                if ultimos4 and limpio.endswith(ultimos4) and 8 <= len(limpio) <= 20:
                    numero = limpio
                    cuenta = "AHORROS"
            break

    return {"CUENTA": cuenta, "NÚMERO": numero}


def extraer_tablas(pdf_path):
    patrones = {
        # SALDO INICIAL puede estar escrito de varias formas
        "SALDO INICIAL": [
            r"SALDO\s+ANTERIOR",
            r"SALDO\s+CIERRE\s+MES\s+ANTERIOR",
        ],

        # MOVIMIENTO DE INGRESOS
        "MOVIMIENTO DE INGRESOS": [
            r"TOTAL\s+ABONOS",
            r"CREDITOS?",
            r"ABONOS",
            r"DEPOSITOS\s+Y\s+OTROS\s+CREDITOS",
        ],

        # MOVIMIENTO DE EGRESOS
        "MOVIMIENTO DE EGRESOS": [
            r"DEBITOS?",
            r"TOTAL\s+CARGOS",
            r"CARGOS?",
            r"RETIROS\s+Y\s+OTROS\s+DEBITOS",
        ],

        # SALDO EN PESOS A FINAL DE MES
        "SALDO EN PESOS A FINAL DE MES": [
            r"SALDO\s+ACTUAL",
            r"SALDO\s+FINAL",
            r"NUEVO\s+SALDO",
            r"SALDO\s+CLOSING",  # por si algún banco lo pone raro
        ]
    }

    #numero_regex = r"(?:\d{1,2}\s+)?[\$]?\s*([\d]{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)"
    # captura números con o sin separadores y decimales
    #numero_regex = r"[\$]?\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?"
    numero_regex = r"[\$]?\s*(?:\d{1,3}(?:[.,]\d{3})*|\d+)?[.,]\d{2}"

    info_tablas = {}
    usados = set()

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if not texto:
                continue

            # ========= Caso especial: línea con todos los saldos juntos =========
            bloque_match = re.search(
                r"SALDO\s+ANTERIOR.*?NUEVO\s+SALDO\s*\n(.+)",
                texto, re.IGNORECASE
            )
            if bloque_match:
                valores = re.findall(numero_regex, bloque_match.group(1))
                if len(valores) >= 4:
                    info_tablas["SALDO INICIAL"] = valores[0].strip()
                    info_tablas["MOVIMIENTO DE INGRESOS"] = valores[1].strip()
                    info_tablas["MOVIMIENTO DE EGRESOS"] = valores[2].strip()
                    info_tablas["SALDO EN PESOS A FINAL DE MES"] = valores[3].strip()
                    usados.update(info_tablas.keys())


            CLAVE_SALDO_FINAL = "SALDO EN PESOS A FINAL DE MES"
            # ========= Caso especial 1: formato "Saldo inicial a 30/Jun/2025 ..." =========
            if "saldo inicial" in texto.lower() and "saldo final" in texto.lower():
                saldo_inicial_match = re.search(r"Saldo\s+inicial.*?:\s*\$?\s*(" + numero_regex + ")", texto, re.IGNORECASE)
                saldo_final_match   = re.search(r"Saldo\s+final.*?:\s*\$?\s*(" + numero_regex + ")", texto, re.IGNORECASE)

                if saldo_inicial_match:
                    info_tablas["SALDO INICIAL"] = saldo_inicial_match.group(1).strip()
                    usados.add("SALDO INICIAL")

                if saldo_final_match:
                    info_tablas[CLAVE_SALDO_FINAL] = saldo_final_match.group(1).strip()
                    usados.add(CLAVE_SALDO_FINAL)

                # Ingresos/Egresos
                ingresos = []
                for label in ["Aportes", "Rendimientos"]:
                    m = re.search(label + r".*?\$?\s*(" + numero_regex + ")", texto, re.IGNORECASE)
                    if m: ingresos.append(m.group(1).strip())
                if ingresos:
                    info_tablas["MOVIMIENTO DE INGRESOS"] = " + ".join(ingresos)
                    usados.add("MOVIMIENTO DE INGRESOS")

                egresos = []
                for label in ["Retiros", "Ajustes", "GMF", "Gravamen", "Retención"]:
                    m = re.search(label + r".*?\$?\s*(" + numero_regex + ")", texto, re.IGNORECASE)
                    if m: egresos.append(m.group(1).strip() if label != "GMF" else m.group(1).strip())
                if egresos:
                    info_tablas["MOVIMIENTO DE EGRESOS"] = " + ".join(egresos)
                    usados.add("MOVIMIENTO DE EGRESOS")


            # ========= Caso especial 2: formato con "Saldo al ... ..... X" y tabla =========
            if "saldo al" in texto.lower() and "saldo final" in texto.lower():
                saldo_al_match = re.search(r"Saldo\s+al\s+\d{1,2}/\d{2}/\d{4}\s+.*?\s*(" + numero_regex + ")", texto, re.IGNORECASE)
                saldo_final_tabla_match = re.search(r"Saldo\s+Final\s+.*?\s*(" + numero_regex + ")", texto, re.IGNORECASE)

                if saldo_al_match:
                    info_tablas["SALDO INICIAL"] = saldo_al_match.group(1).strip()
                    usados.add("SALDO INICIAL")

                if saldo_final_tabla_match:
                    info_tablas[CLAVE_SALDO_FINAL] = saldo_final_tabla_match.group(1).strip()
                    usados.add(CLAVE_SALDO_FINAL)

                # Ingresos
                ingresos = []
                for label in [r"Depositos\s+y\s+Notas\s+Credito", r"Intereses\s+pagados"]:
                    m = re.search(label + r".*?(" + numero_regex + ")", texto, re.IGNORECASE)
                    if m: ingresos.append(m.group(1).strip())
                if ingresos:
                    info_tablas["MOVIMIENTO DE INGRESOS"] = " + ".join(ingresos)
                    usados.add("MOVIMIENTO DE INGRESOS")

                # Egresos
                egresos = []
                for label in [r"Cheques\s+Pagados", r"Comisiones", r"Impuestos", r"Retiros\s+y\s+Notas\s+Debito"]:
                    m = re.search(label + r".*?(" + numero_regex + ")", texto, re.IGNORECASE)
                    if m: egresos.append(m.group(1).strip())
                if egresos:
                    info_tablas["MOVIMIENTO DE EGRESOS"] = " + ".join(egresos)
                    usados.add("MOVIMIENTO DE EGRESOS")



            for clave, lista_patrones in patrones.items():
                if clave in usados:
                    continue
                for patron in lista_patrones:
                    # buscamos el bloque de texto desde el patrón en adelante
                    regex = rf"{patron}.*?(?:{numero_regex}(?:\s+{numero_regex})*)"
                    match = re.search(regex, texto, re.IGNORECASE | re.DOTALL)
                    if match:
                        # extraemos todos los números del bloque
                        valores = re.findall(numero_regex, match.group(0))
                        if valores:
                          candidatos = [v for v in valores if re.search(r"[.,]\d{2}$", v.strip())]
                          if candidatos:
                            valor = candidatos[-1]  # el último es el saldo real
                            info_tablas[clave] = valor.strip()
                            usados.add(clave)
                            #print(f"[DEBUG] {clave} → '{match.group(0)}' → {valor}")
                            break

    for clave in patrones:
        if clave not in info_tablas:
            info_tablas[clave] = "No encontrado"

    # ========= Ordenar diccionario final =========
    orden_claves = [
        "SALDO INICIAL",
        "MOVIMIENTO DE INGRESOS",
        "MOVIMIENTO DE EGRESOS",
        "SALDO EN PESOS A FINAL DE MES"
    ]
    info_tablas_ordenado = {clave: info_tablas[clave] for clave in orden_claves}

    return info_tablas_ordenado



def normalizar_numero(valor: str):
    if not valor or str(valor).strip() in ["", ".", ","]:
        return None

    limpio = str(valor).replace("$", "").replace(" ", "").strip()

    # Si tiene miles con coma y decimal con punto: 623,548.25
    if re.match(r"^\d{1,3}(?:,\d{3})*\.\d{2}$", limpio):
        limpio = limpio.replace(",", "")  # quitar separador de miles
    # Si tiene miles con punto y decimal con coma: 623.548,25
    elif re.match(r"^\d{1,3}(?:\.\d{3})*,\d{2}$", limpio):
        limpio = limpio.replace(".", "").replace(",", ".")  # convertir decimal a punto
    # Solo coma como decimal: 12345,25
    elif "," in limpio and "." not in limpio:
        limpio = limpio.replace(",", ".")
    # Solo punto como decimal: 12345.25
    # de lo contrario, dejarlo como está

    try:
        return float(limpio)
    except ValueError:
        return None
    

def exportar_a_excel(resultados, plantilla_path, output_path):
    wb = load_workbook(plantilla_path)
    hoja = wb.worksheets[2]  # tercera hoja
    fila_inicio = 11

    for i, res in enumerate(result55tados):
        fila = fila_inicio + i

        # Texto
        hoja[f"D{fila}"] = res["texto"].get("CUENTA", "")
        hoja[f"F{fila}"] = res["texto"].get("NÚMERO", "")

        # Tablas (aseguramos que haya 4 valores)
        valores_tabla = list(res["tablas"].values())[:4]
        for j, val in enumerate(valores_tabla):
            col = chr(ord("I") + j)  # I, J, K, L
            numero = normalizar_numero(val)
            hoja[f"{col}{fila}"] = numero if numero is not None else val


    # Guardar archivo final
    wb.save(output_path)
    print(f"Archivo exportado: {output_path}")
