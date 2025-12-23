# Emociones IA Frontend

Aplicación React que consume el backend Flask (JWT + análisis de texto) para registrar usuarios, autenticarse, ejecutar análisis de sentimiento y visualizar métricas en un dashboard.

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

- `POST /register`
- `POST /login`
- `POST /analyze-text`
- `GET /profile`
- `GET /dashboard`

Todos los requests autenticados envían el encabezado `Authorization: Bearer <token>` mediante el interceptor configurado en `src/services/api.js`.
