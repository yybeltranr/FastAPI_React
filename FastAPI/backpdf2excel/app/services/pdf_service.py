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
        whole_text = all_text.replace('\xa0', ' ')
        whole_text = re.sub(r'[\u200B-\u200D\uFEFF]', '', whole_text)   # zero-width
        # opcional: colapsar espacios múltiples
        whole_text = re.sub(r'[ \t]{2,}', '  ', whole_text)  # conserva "columnas" con varios espacios

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
            numero_en_nombre = max(m_cuenta, key=len)
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
                r"Cuenta\s*no\.?\s*\n\s*([\d]{2,6}(?:-\d{2,10})+)", #Cuenta no. minúsculas con salto y guion
                r"CUENTA\s+DE\s+AHORROS\s*\n\s*([\d\s]{6,40})", # Davivienda (con espacios y salto)
                r"CUENTA\s+DE\s+AHORROS\s*([\d\s]{6,40})", # Davivienda (con espacios, sin salto)
                r"CUENTA\s+No\.?\s*\n\s*([\d\s\-]{6,30})", # CUENTA No. con salto
                r"CUENTA\s+No\.?\s*([\d\-]+)",         # CUENTA No. inline con separadores -
                r"CUENTA\s+No\.?\s*(\d+)",            # CUENTA No. inline
                r"No\.?\s+([\d\-]{6,30})",
                r"((?:\d(?:[\s\-\.\u00A0]?)){6,19}\d)",
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

        # Caso especial: formato "Cuenta no." en una línea y el número en la siguiente
        if info_textual.get("NÚMERO") == "No encontrado":
            m = re.search(r"Cuenta\s*no\.?\s*\n\s*([\d]{2,6}(?:-\d{2,10})+)", whole_text, re.IGNORECASE)
            if m:
                val = m.group(1)
                limpio = re.sub(r"[^\d]", "", val)  # limpiar guiones y espacios
                info_textual["NÚMERO"] = limpio

        if info_textual["CUENTA"] == "No encontrado" and info_textual["NÚMERO"] == "No encontrado":
            # Caso especial Davivienda
            davivienda_info = extraer_davivienda(lines, ultimos4)
            info_textual.update(davivienda_info)

        if info_textual["CUENTA"] == "AHORROS":
            info_textual["CUENTA"] = "1 Ahorros" 
        if info_textual["CUENTA"] == "CORRIENTE":
            info_textual["CUENTA"] = "2 Corriente"

        return info_textual

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
            r"INTERESES\s+RECIBIDOS",
            r"Más\s+Créditos",
        ],

        # MOVIMIENTO DE EGRESOS
        "MOVIMIENTO DE EGRESOS": [
            r"DEBITOS?",
            r"TOTAL\s+CARGOS",
            r"CARGOS?",
            r"RETIROS\s+Y\s+OTROS\s+DEBITOS",
            r"\bIVA\b",
            r"4\s*POR\s*MIL",
            r"RETENCIONES?",
            r"Menos\s+Débitos",
        ],

        # SALDO EN PESOS A FINAL DE MES
        "SALDO EN PESOS A FINAL DE MES": [
            r"SALDO\s+ACTUAL",
            r"SALDO\s+FINAL",
            r"NUEVO\s+SALDO",
            r"SALDO\s+CLOSING",  # por si algún banco lo pone raro
        ]
    }

    info_tablas = {}

    #numero_regex = r"(?:\d{1,2}\s+)?[\$]?\s*([\d]{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)"
    # captura números con o sin separadores y decimales
    #numero_regex = r"[\$]?\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?"
    #numero_regex = r"[\$]?\s*(?:\d{1,3}(?:[.,]\d{3})*|\d+)?[.,]\d{2}"
    #numero_regex = r"(?<!\w)[\$]?\s*\d*(?:[.,]\d{3})*(?:[.,]\d{2})(?!\w)"
    #numero_regex = r"(?<!\w)[\$]?\s*(?:\d{1,2}\s+)?(?:\d{1,3}(?:[.,]\d{3})*|)(?:[.,]\d{2})(?!\w)"
    #numero_regex = r"(?<!\w)[\$]?\s*(?:\d{1,2}(?![.,])\s+)?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})(?!\w)"
    #numero_regex = r"(?<!\w)(?:\$?\s*(?:\d{1,2}(?![.,])\s+)?)((?:\d{1,3}(?:[.,]\d{3})*)(?:[.,]\d{2})?|[.,]\d{2})(?!\w)"
    numero_regex = (
        r"(?<!\w)"                                   # no pegado a palabra a la izquierda
        r"(?:\$?\s*(?:\d{1,2}(?![.,])\s+)?)"         # columna intermedia opcional (1-2 dígitos) NO seguida de . o ,
        r"("                                         # <-- único grupo de captura: el monto
        r"(?:\d{1,3}(?:[.,]\d{3})*)"               # entero con separadores de miles opcionales
        r"(?:[.,]\d{2})?"                          # decimal opcional (si existe, 2 dígitos)
        r"|[.,]\d{2}"                              # o decimal-only (.56 o ,56)
        r")"
        r"(?!\w)"
    )

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
                saldo_inicial_match = re.search(r"Saldo\s+inicial(?:\s+a\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4})?\s*[:\-]?\s*\$?\s*(" + numero_regex + ")", texto, re.IGNORECASE)
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
                    #m = re.search(label + r".*?\$?\s*(" + numero_regex + ")", texto, re.IGNORECASE)
                    m = re.search(label + r".*?\$?\s*" + numero_regex, texto, re.IGNORECASE)
                    if m: ingresos.append(m.group(1).strip())
                if ingresos:
                    info_tablas["MOVIMIENTO DE INGRESOS"] = " + ".join(ingresos)
                    usados.add("MOVIMIENTO DE INGRESOS")

                egresos = []
                for label in ["Retiros", "Ajustes", "GMF", "Gravamen", "Retención"]:
                    #m = re.search(label + r".*?\$?\s*(" + numero_regex + ")", texto, re.IGNORECASE)
                    m = re.search(label + r".*?\$?\s*" + numero_regex, texto, re.IGNORECASE)
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
                encontrados = []
                for patron in lista_patrones:
                    #regex = rf"{patron}.*?(?:{numero_regex}(?:\s+{numero_regex})*)"
                    regex = rf"{patron}\s*[:\-]?\s*[\$]?\s*{numero_regex}"
                    match = re.search(regex, texto, re.IGNORECASE | re.DOTALL)
                    if match:
                        valores = re.findall(numero_regex, match.group(0))
                        if valores:
                            candidatos = [v.strip() for v in valores if re.search(r"[.,]\d{2}$", v.strip())]
                            if candidatos:
                                # guardamos el patrón que generó el valor
                                encontrados.append((patron, candidatos[-1]))

                if encontrados:
                    # Extraer solo los valores
                    solo_valores = [val for _, val in encontrados]
                    # Eliminar duplicados manteniendo orden
                    solo_valores = list(dict.fromkeys(solo_valores))

                    if clave in ["MOVIMIENTO DE INGRESOS", "MOVIMIENTO DE EGRESOS"]:
                        if len(solo_valores) == 1:
                            # solo un valor (aunque venga de 2 patrones iguales) → mostrar solo 1
                            info_tablas[clave] = solo_valores[0]
                        else:
                            # varios valores distintos → concatenar
                            info_tablas[clave] = " + ".join(solo_valores)
                    else:
                        info_tablas[clave] = solo_valores[-1]

                    usados.add(clave)
                            

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

def find_sequential_words_coords_all(pdf_path, word1, word2, word3, y_tolerance=1):
    """
    Busca tres palabras secuenciales en la misma línea en todo el documento.
    Retorna una lista de tuplas, donde cada tupla contiene el número de página y las coordenadas
    de la palabra del medio.

    Args:
        pdf_path (str): La ruta al archivo PDF.
        word1 (str): La primera palabra a buscar.
        word2 (str): La segunda palabra a buscar.
        word3 (str): La tercera palabra a buscar.
        y_tolerance (float): La tolerancia en el eje Y para considerar que las palabras están en la misma línea.

    Returns:
        list: Una lista de tuplas. Cada tupla es (page_number, (x0, top, x1, bottom)).
              Retorna una lista vacía si no se encuentra la secuencia.
    """
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            for i in range(len(words) - 2):
                current_word = words[i]
                next_word = words[i+1]
                next_next_word = words[i+2]

                # Comprobar si las palabras coinciden
                if (current_word['text'] == word1 and
                    next_word['text'] == word2 and
                    next_next_word['text'] == word3):

                    # Comprobar si están en la misma línea usando la tolerancia y
                    if (abs(next_word['top'] - current_word['top']) <= y_tolerance and
                        abs(next_next_word['top'] - current_word['top']) <= y_tolerance):

                        page_number = page.page_number
                        coords = (next_word['x0'], next_word['top'], next_word['x1'], next_word['bottom'])
                        results.append((page_number, coords))
    return results

def get_numbers_below_coordinates(pdf_path, coordinates_list):
    """
    Busca y retorna las palabras que se encuentran por debajo de una lista de coordenadas,
    filtrando solo los números con el formato especificado.

    Args:
        pdf_path (str): La ruta al archivo PDF.
        coordinates_list (list): Una lista de tuplas en el formato (page_number, (x0, top, x1, bottom)).

    Returns:
        dict: Un diccionario donde la clave es el número de página y el valor es una lista
              de strings que cumplen con el formato numérico.
    """
    results = {}

    coords_by_page = {}
    for page_num, coords in coordinates_list:
        if page_num not in coords_by_page:
            coords_by_page[page_num] = []
        coords_by_page[page_num].append(coords)

    # Expresión regular para números con formato de miles y decimales.
    number_pattern = re.compile(
    r'^\$?'
    r'-?'
    r'[\d,.]+'
    r'\+?'
    r'$'
    )

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            if page_number in coords_by_page:
                all_words = page.extract_words()
                page_numbers = []

                for x0_ref, _, x1_ref, y1_ref in coords_by_page[page_number]:
                    for word in all_words:
                        word_x0 = word['x0']
                        word_x1 = word['x1']
                        word_y1 = word['bottom']

                        # Condición 1: El 'y' de la palabra debe estar por debajo del 'y' de referencia
                        is_below = word_y1 > y1_ref

                        # Condición 2: La palabra debe estar en el "carril" vertical de la columna de referencia.
                        # Asumimos que la columna tiene un ancho de 50 puntos a la izquierda y 50 a la derecha
                        # de las coordenadas del encabezado.
                        x_in_column = (word_x0 >= x0_ref - 50) and (word_x1 <= x1_ref + 50)

                        # Condición 3: La palabra debe coincidir con el patrón numérico
                        is_number = number_pattern.match(word['text'])

                        if is_below and x_in_column and is_number:
                            page_numbers.append(word['text'])

                if page_numbers:
                    results[page_number] = page_numbers
    return results

def format_number_with_commas(number):
    """
    Formatea un número (float o int) a una cadena con puntos como separadores
    de miles y una coma como separador decimal. Quita el signo negativo.
    Ejemplo: 2.302.353,40
    """
    if not isinstance(number, (int, float)):
        return None

    # 1. Quitar el signo negativo y formatear con 2 decimales y coma como decimal
    number = abs(number)
    formatted_number = f"{number:,.2f}"

    # 2. Reemplazar los separadores
    # El formato por defecto de Python es con coma (,) para miles y punto (.) para decimales.
    # Necesitamos revertir eso.
    # Paso a paso:
    # a. Reemplazamos la coma por un carácter temporal (ej. 'X') para evitar conflictos.
    # b. Reemplazamos el punto por la coma.
    # c. Reemplazamos el carácter temporal por el punto.
    
    formatted_number = formatted_number.replace(",", "X").replace(".", ",").replace("X", ".")
    
    return formatted_number

def clean_number_string(number_str):
    """
    Limpia un string de caracteres no numéricos como $, +, y espacios.
    """
    cleaned = number_str.strip().replace('$', '').replace('+', '').strip()
    return cleaned

def find_max_absolute_value(data_dict):
    """
    Encuentra el valor numérico con el valor absoluto más grande en un diccionario
    de listas de strings, manejando diferentes formatos de números.
    """
    max_value = None

    for page_numbers in data_dict.values():
        for number_str in page_numbers:
            try:
                # 1. Limpiar el string de símbolos no numéricos
                cleaned_str = clean_number_string(number_str)

                # 2. Lógica para determinar el formato de los separadores
                last_period = cleaned_str.rfind('.')
                last_comma = cleaned_str.rfind(',')

                if last_comma > last_period:
                    # Formato europeo/latinoamericano: '1.234,56'
                    cleaned_final = cleaned_str.replace('.', '').replace(',', '.')
                elif last_period > last_comma:
                    # Formato estadounidense: '1,234.56'
                    cleaned_final = cleaned_str.replace(',', '')
                else:
                    # Formato sin separadores o con solo uno
                    cleaned_final = cleaned_str

                # 3. Convertir el string limpio a un número flotante
                current_value = float(cleaned_final)

                # 4. Comparar y actualizar el valor máximo
                if max_value is None or abs(current_value) > abs(max_value):
                    max_value = current_value
            except ValueError:
                continue

    return max_value

def encontrar_maximo_movimiento(pdf_path, banco):
    listado_bancos=["24 Bancolombia", "30 BBVA Colombia", "15 Banco de Occidente", "6 Banco Davivienda", "36 Colpatria Red Multibanca", "48 ITAÚ BBA Colombia S.A.", "2 Banagrario"]
    if banco not in listado_bancos:
        return "Banco no encontrado"

    word1 = ""
    word2 = ""
    word3 = ""

    if banco == "24 Bancolombia":
        word1 = "DCTO."
        word2 = "VALOR"
        word3 = "SALDO"
    elif banco == "30 BBVA Colombia":
      #los encabezados de las paginas no tienen capa de texto
        word1 = "DE"
        word2 = "AHORROS"
        word3 = "EMPRESARIAL"
    elif banco == "36 Colpatria Red Multibanca":
        word1 = "DESCRIPCION"
        word2 = "MONTO"
        word3 = "SALDO"
    elif banco == "6 Banco Davivienda":
        word1 = "Fecha"
        word2 = "Valor"
        word3 = "Doc."
    elif banco == "15 Banco de Occidente":
      #asumo que solo se usan los creditos, no se si tambien debitos
        word1 = "DEBITOS"
        word2 = "CREDITOS"
        word3 = "SALDO"

    coordenadas_encontradas = find_sequential_words_coords_all(pdf_path, word1, word2, word3)
    if not coordenadas_encontradas:
        return "No se encontraron las coordenadas de los encabezados de la tabla."

    numeros_encontrados = get_numbers_below_coordinates(pdf_path, coordenadas_encontradas)

    if not numeros_encontrados:
        return "No se encontraron números válidos en el PDF para el banco especificado."

    max_abs_value = find_max_absolute_value(numeros_encontrados)

    return format_number_with_commas(max_abs_value)

def exportar_a_excel(resultados, valores_frontend, fecha_conciliacion, fecha_cierre, responsable_cargo, poliza, plantilla_path, output_path):
    wb = load_workbook(plantilla_path)
    hoja = wb.worksheets[2]  # tercera hoja
    fila_inicio = 11
    fila = fila_inicio

    for banco_nombre, archivos in resultados.items():
        for idx, archivo in enumerate(archivos):
            keyArchivo = f"{banco_nombre}-{idx}"
            valores = valores_frontend.get(keyArchivo, {})

            # Subcuenta
            subcuenta = valores.get("subcuenta", {})
            hoja[f"C{fila}"] = f"{subcuenta.get('id', '')} {subcuenta.get('nombre', '')}".strip()

            # Texto extraído
            hoja[f"D{fila}"] = archivo["resultado"]["texto"].get("CUENTA", "")
            hoja[f"F{fila}"] = archivo["resultado"]["texto"].get("NÚMERO", "")

            # Nombre del accordion (banco)
            hoja[f"E{fila}"] = banco_nombre
           
            # Moneda enviada desde frontend
            moneda = valores.get("moneda", {})
            hoja[f"G{fila}"] = f"{moneda.get('id', '')} {moneda.get('nombre', '')}".strip()

            # Utilización
            hoja[f"H{fila}"] = valores.get("utilizacionTexto", "")

            # Tablas (4 columnas)
            tablas = archivo["resultado"].get("tablas", {})
            for j, val in enumerate(list(tablas.values())[:4]):
                col = chr(ord("I") + j)  # I, J, K, L
                hoja[f"{col}{fila}"] = normalizar_numero(val) if normalizar_numero(val) is not None else val

            # Max_movimiento
            hoja[f"M{fila}"] = archivo["resultado"].get("max_movimiento", "")

            # Tasa
            hoja[f"N{fila}"] = valores.get("tasa", "")

            # Responsable / Cargo
            hoja[f"O{fila}"] = responsable_cargo

            # Póliza
            hoja[f"P{fila}"] = poliza

            # Fecha constitución
            hoja[f"Q{fila}"] = valores.get("fecha", "")

            # Fecha cierre
            hoja[f"R{fila}"] = fecha_cierre.split('T')[0].replace("-", "/") if fecha_cierre else ""

            # Fecha conciliación
            hoja[f"S{fila}"] = fecha_conciliacion.split('T')[0].replace("-", "/") if fecha_conciliacion else ""

            # Observaciones
            hoja[f"T{fila}"] = valores.get("observaciones", "")

            fila += 1

    wb.save(output_path)
    print(f"Archivo exportado: {output_path}")
