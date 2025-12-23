# Backend (Flask + MySQL + IA)

## Requisitos
- Python 3.11+
- MySQL 8+ (cualquier variante compatible con `mysql+pymysql`)

## Instalación rápida
1. Crear y activar un entorno virtual.
2. Instalar dependencias: `pip install -r backend/requirements.txt`.
3. Descargar los recursos de TextBlob una sola vez: `python -m textblob.download_corpora`.
4. Copiar `.env` y ajustar credenciales de base de datos y llaves JWT.
5. Crear base de datos vacía (`ia_dashboard` por defecto) y exportar variable `FLASK_APP=app.py` si usas los comandos de Flask.
6. Inicializar migraciones (opcional, pero recomendado):
   ```bash
   flask db init
   flask db migrate -m "Initial tables"
   flask db upgrade
   ```
7. Ejecutar el servidor: `python backend/app.py` o `flask run`.

## Variables de entorno principales
- `DATABASE_URL`: `mysql+pymysql://user:pass@host:3306/db_name`
- `SECRET_KEY` y `JWT_SECRET_KEY`: claves seguras para sesiones y tokens.
- `ANALYTICS_LIMIT`: máximo de registros recientes devueltos en `/dashboard`.

## Endpoints principales

### Autenticación
| Método | Ruta              | Descripción                        | Autenticación |
| ------ | ----------------- | ---------------------------------- | ------------- |
| POST   | /register         | Registro de usuario                | No            |
| POST   | /api/register     | Registro de usuario (API)          | No            |
| POST   | /login            | Login y obtención de JWT           | No            |
| POST   | /api/login        | Login y obtención de JWT (API)     | No            |

### Perfil de usuario
| Método | Ruta      | Descripción                  | Autenticación |
| ------ | --------- | ----------------------------| ------------- |
| GET    | /profile  | Obtener datos del usuario    | JWT           |
| PUT    | /profile  | Actualizar datos del usuario | JWT           |



### Media (imágenes, videos, webcam)
| Método | Ruta                              | Descripción                        | Autenticación |
| ------ | ---------------------------------- | ---------------------------------- | ------------- |
| GET    | /media/model-metadata             | Metadatos del modelo de IA         | Opcional      |
| POST   | /analyze-image                    | Analiza imagen subida              | JWT           |
| POST   | /analyze-video                    | Analiza video subido               | JWT           |
| POST   | /analyze-webcam                   | Analiza captura de webcam          | JWT           |
| POST   | /media/live-session/start         | Inicia sesión en vivo              | JWT           |
| POST   | /media/live-session/stop          | Finaliza sesión en vivo            | JWT           |
| POST   | /analyze-webcam-frame             | Analiza fotograma de webcam        | JWT           |
| GET    | /media/records                    | Listado de análisis multimedia     | JWT           |
| GET    | /media/files/<path:relative_path> | Descarga archivos multimedia       | JWT           |

## Instalación y ejecución

1. Clona el repositorio y entra a la carpeta del backend.
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
4. Configura las variables de entorno en un archivo `.env` (ver ejemplo en el repo).
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

## Notas
- El backend debe estar corriendo antes de iniciar el frontend.
- Revisa los endpoints y sus parámetros en este README para integración.
    "id": 5,
    "sentiment_label": "positive",
    "polarity": 0.52,
    "subjectivity": 0.65,
    "summary": "Positive sentiment detected: ...",
    "created_at": "2025-12-20T23:59:01.414Z"
  },
  "message": "Text analyzed successfully."
}
```

## Dashboard
La ruta `/dashboard` agrega toda la información necesaria para construir el dashboard en Postman o en un frontend dedicado:
- Totales de usuarios y análisis.
- Conteo de resultados por etiqueta de sentimiento.
- Últimos `ANALYTICS_LIMIT` análisis realizados.
