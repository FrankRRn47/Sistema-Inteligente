
# Sistema Inteligente: Reconocimiento de Emociones

Este sistema integra un backend profesional en Flask (Python) y un frontend moderno en React (HTML/CSS/JS), junto con un modelo de inteligencia artificial para el reconocimiento de emociones faciales y análisis de texto.

## Frontend (React + HTML/CSS/JS)
Interfaz responsiva y moderna que permite:
- Registro y autenticación de usuarios
- Análisis de emociones en imágenes, videos y texto
- Visualización de resultados y métricas en dashboards interactivos
- Integración segura con el backend mediante API REST y JWT

## Backend (Flask + MySQL + JWT)
Servicios robustos para:
- Gestión de usuarios y autenticación
- Procesamiento y análisis de imágenes, videos y texto
- Almacenamiento seguro de resultados y archivos multimedia
- Exposición de endpoints REST para integración con el frontend

### Endpoints principales
**Autenticación:**
- POST /register
- POST /api/register
- POST /login
- POST /api/login

**Perfil de usuario:**
- GET /profile
- PUT /profile

**Media (imágenes, videos, webcam):**
- GET /media/model-metadata
- POST /analyze-image
- POST /analyze-video
- POST /analyze-webcam
- POST /media/live-session/start
- POST /media/live-session/stop
- POST /analyze-webcam-frame
- GET /media/records
- GET /media/files/<path:relative_path>

## Especificaciones del modelo de IA (tracked)
- El modelo principal es una CNN entrenada sobre el dataset FER2013 (Kaggle), con 35,887 imágenes de 48x48 píxeles.
- Las clases de emociones reconocidas son: angry, disgust, fear, happy, neutral, sad, surprise.
- El archivo `model_weights.h5` contiene los pesos entrenados del modelo.
- El sistema permite entrenamiento y evaluación mediante los scripts en `tracked_train_files`.
- Los resultados y métricas se almacenan en la carpeta `plots`.
- El sistema soporta ejecución en GPU (recomendado) y CPU.

## Instalación y ejecución

### Backend
1. Clona el repositorio y entra a la carpeta `backend`.
2. Crea y activa un entorno virtual:
	```bash
	python -m venv .venv
	.venv\Scripts\activate  # Windows
	source .venv/bin/activate  # Linux/Mac
	```
3. Instala dependencias:
	```bash
	pip install -r requirements.txt
	```
4. Configura las variables de entorno en `.env`.
5. Inicializa la base de datos y migraciones:
	```bash
	flask db init
	flask db migrate -m "Initial tables"
	flask db upgrade
	```
6. Ejecuta el backend:
	```bash
	python app.py
	```

### Frontend
1. Entra a la carpeta `frontend`.
2. Copia `.env.example` a `.env` y ajusta la variable `REACT_APP_API_BASE_URL`.
3. Instala dependencias:
	```bash
	npm install
	```
4. Ejecuta la aplicación:
	```bash
	npm start
	```

### Modelo de IA (tracked)
- Para ejecutar el reconocimiento de emociones, asegúrate de tener los archivos de pesos y recursos en la carpeta `tracked`.
- Para entrenamiento, descarga el dataset FER2013 y sigue las instrucciones en los scripts de `tracked_train_files`.
- Puedes usar el entorno Anaconda y el archivo `tf-gpu.yaml` para instalar todas las dependencias necesarias.