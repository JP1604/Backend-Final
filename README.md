# Backend-Final

This project contains a FastAPI backend and a React + Vite frontend for a simple Online Judge system.

## Running everything with Docker Compose (recommended)

Build and start the whole stack:

```powershell
# Build and start all services
docker-compose up -d --build

# Show logs for services
docker-compose logs -f
```

- Frontend (static site served by Nginx): http://localhost:8080
- Backend API (FastAPI): http://localhost:8008

## Local development

### Backend

Run the backend directly with Python (requires dependencies in `requirements.txt`):

```powershell
# Install dependencies
pip install -r requirements.txt

# Start backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

This will map the API at http://localhost:8000 inside containers; if using Docker Compose, the API is exposed at host port 8008.

### Frontend

Install frontend dependencies and run Vite dev server:

```powershell
cd frontend
npm install
npm run dev
```

The dev server listens on http://localhost:5173 by default. When using `npm run dev` with the backend running in Docker at host port 8008, the frontend will call `http://localhost:8008` by default.

### Build and serve frontend locally (production build)

```powershell
cd frontend
npm run build
npx serve -s dist -p 8080
```

> Use `VITE_API_URL` env var when building the frontend to point to the backend. For example, when building a container or building locally to be served with Nginx (production):
>
> ```powershell
> # Build the frontend with a relative API base
> set VITE_API_URL=/api
> npm run build
> ```

## Notes on integration

- The frontend's API base URL is configured using the Vite env var `VITE_API_URL` (accessed in code via `import.meta.env.VITE_API_URL`).
- For development outside Docker, the default base URL falls back to `http://localhost:8008` so a local Vite dev server can reach the API running in Docker.
- For Docker-based deployment, the frontend is built with `VITE_API_URL=/api` and served by Nginx; Nginx proxies `/api` to the backend service by container name `api:8000`.
- CORS is enabled on the backend (development) to allow requests from the frontend.

## Troubleshooting tips
- If frontend doesn't appear, verify no local dev server is binding to the mapped port (for example, port 5173 already used by the dev server). Docker mapping uses 8080 for the built frontend.
- If the API returns CORS errors in dev, make sure the backend is running and CORS is allowed (in `src/main.py`, it's already set to allow all origins).


---

If you want, I can also:
- Add a `Makefile` or `scripts` to streamline common tasks like `make dev`.
- Add a `docker-compose.override.yml` for development with volume mounts and `npm run dev` instead of building the static assets.
