# Usa una imagen base de Python
FROM python:3.8-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos de la aplicación al contenedor
COPY . /app

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto en el que Flask está corriendo
EXPOSE 8080

# Comando para ejecutar la aplicación usando gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]



