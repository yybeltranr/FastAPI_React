# Usar una imagen base de Python
FROM python:3.11-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar el archivo de requerimientos e instalar dependencias
COPY requeriments.txt requeriments.txt
RUN pip install --no-cache-dir -r requeriments.txt

# Copiar el resto de la aplicación
COPY ./app /app/app

# Exponer el puerto en el que corre la aplicación
EXPOSE 8000

# Comando para iniciar la aplicación con Uvicorn
# El host 0.0.0.0 es crucial para que sea accesible desde fuera del contenedor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
