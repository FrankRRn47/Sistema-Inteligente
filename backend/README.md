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

## Endpoints
| Método | Ruta | Descripción | Autenticación |
| --- | --- | --- | --- |
| POST | `/register` | Crea un usuario y devuelve JWT | No |
| POST | `/login` | Autentica y devuelve JWT | No |
| GET | `/profile` | Obtiene datos del usuario actual | Bearer JWT |
| PUT | `/profile` | Actualiza nombre y contraseña | Bearer JWT |
| POST | `/analyze-text` | Analiza texto con TextBlob y persiste resultado | Bearer JWT |
| GET | `/dashboard` | Resumen de usuarios, análisis y últimos resultados | Bearer JWT |
| GET | `/health` | Verificación básica del servicio | No |

### Respuesta muestra `/analyze-text`
```json
{
  "analysis": {
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
