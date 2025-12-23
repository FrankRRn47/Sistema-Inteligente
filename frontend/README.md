
# Frontend (React + HTML/CSS/JS):

Este frontend profesional está desarrollado en React y utiliza HTML, CSS y JavaScript moderno para ofrecer una interfaz intuitiva y responsiva. Permite a los usuarios registrarse, autenticarse, analizar emociones en imágenes, videos y texto, y visualizar resultados en tiempo real mediante dashboards interactivos. La integración con el backend Flask se realiza mediante API REST y autenticación JWT, garantizando seguridad y escalabilidad.

## Requisitos

- Node.js 18+
- Backend en ejecución (ver `backend/README.md`) y accesible mediante la URL definida en `REACT_APP_API_BASE_URL`.

## Instalación

```bash
cd frontend
cp .env.example .env     # Ajusta la URL del backend
npm install
npm start
```

## Estructura

```
src/
  components/      # UI reusable (cards, navbar, rutas protegidas)
  context/         # AuthProvider y estado global
  hooks/           # Custom hooks para autenticación
  pages/           # Vistas: Login, Register, TextAnalyzer, Dashboard
  services/        # Clientes Axios + integración API
  styles/          # CSS global y tokens
```


## Endpoints utilizados

### Autenticación
- POST /register
- POST /login
- GET /profile

### Media (imágenes, videos, webcam)
- POST /media/live-session/start
- POST /media/live-session/stop
- GET /media/model-metadata
- GET /media/records
- GET /media/files/<path:relative_path>
- POST /analyze-image
- POST /analyze-video
- POST /analyze-webcam
- POST /analyze-webcam-frame

Todos los requests autenticados envían el encabezado `Authorization: Bearer <token>` mediante el interceptor configurado en `src/services/api.js`.

## Instalación y ejecución

1. Clona el repositorio y entra a la carpeta del frontend.
2. Copia el archivo `.env.example` a `.env` y ajusta la variable `REACT_APP_API_BASE_URL` con la URL del backend.
3. Instala dependencias:
  ```bash
  npm install
  ```
4. Ejecuta la aplicación:
  ```bash
  npm start
  ```

## Notas
- El backend debe estar corriendo antes de iniciar el frontend.
- Revisa los endpoints y sus parámetros en este README para integración.
