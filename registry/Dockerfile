# Uso de una imagen base Python
FROM python:3.9-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar el archivo de requisitos y luego instalar las dependencias
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del directorio del registro al directorio de trabajo
COPY . .

# Definir el puerto en el que se expondrá el contenedor
EXPOSE 8080

# El comando para ejecutar la aplicación
CMD ["python", "registry.py"]
