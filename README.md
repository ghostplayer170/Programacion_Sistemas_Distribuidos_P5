# Programacion_Sistemas_Distribuidos_P5

## Gestión Dinámica de Coordinadores en Sistemas Distribuidos

Este proyecto implementa un sistema distribuido utilizando Docker y Flask para manejar el registro de nodos, los procesos de elección y la asignación dinámica de coordinadores dentro de un clúster.

## Características

- **Registro de Nodos**: Automatiza el registro de nuevos nodos en el sistema.
- **Heartbeats**: Mantiene un control de la actividad de los nodos mediante señales periódicas.
- **Elección de Coordinadores**: Inicia automáticamente una elección para seleccionar un nuevo coordinador cuando sea necesario.

## Tecnologías Utilizadas

- **Flask**: Para crear la API que gestiona las interacciones entre los nodos.
- **Docker**: Utilizado para contenerizar y desplegar cada instancia del servicio de manera aislada.

## Arquitectura del Sistema

El siguiente diagrama ilustra la arquitectura del sistema distribuido utilizando Docker:

![Arquitectura del Sistema](https://files.catbox.moe/sfkrbn.png)

#### Descripción del Diagrama

- **Cliente**: Interactúa con Docker a través de comandos como `docker run`, `docker build`, y `docker pull`.
- **Docker Host**: Aloja el daemon de Docker y gestiona imágenes y contenedores.
   - **Imágenes**: Incluye varias imágenes Docker como `Nodo0`, `Nodo1`, `Nodo2`, y `Registry`, cada una mapeada a diferentes puertos.
   - **Contenedores**: Ejecuta un contenedor específico que coordina las acciones entre nodos.
- **App-network**: Red interna de Docker que permite la comunicación entre nodos y el registro.

Esta estructura facilita la escalabilidad y gestión de servicios dentro del clúster, permitiendo una eficiente elección de coordinadores y manejo de nodos en el sistema.


## Estructura del Proyecto

```
/coordinator-docker        # Directorio raíz del proyecto.
├── node/
│   ├── node.py            # Implementación de la lógica del nodo.
│   ├── Dockerfile         # Instrucciones para construir la imagen Docker del servicio.
│   └── requirements.txt   # Dependencias de Python.
├── registry/
│   ├── registry.py        # Implementación de la lógica del registro.
│   ├── Dockerfile         # Instrucciones para construir la imagen Docker del servicio.
│   └── requirements.txt   # Dependencias de Python.
├── docker-compose.yml     # Define los servicios, redes y volúmenes para Docker.
└── README.md              # Documentación del proyecto.
```

## Instalación

Para poner en marcha el proyecto localmente, sigue estos pasos:

1. **Clona el repositorio:**

   ```bash
   git clone https://github.com/tu-usuario/tu-repositorio.git
   cd tu-repositorio
   ```

2. **Construye las imágenes Docker:**

   ```bash
   docker-compose build
   ```

3. **Despliega los servicios:**

   ```bash
   docker-compose up
   ```

