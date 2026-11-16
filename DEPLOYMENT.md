# ALPR Indonesia Deployment

This project is a FastAPI ASGI backend plus a Vue/Vite SPA. It is not a Laravel
or PHP runtime project.

## Recommended Demo Path: ASGI + SPA Single App

Use an ASGI host for the backend so FastAPI lifespan startup and WebSocket routes
work correctly.

1. Build the frontend:

```bash
cd frontend
npm ci
npm run build
```

The Vite build writes the SPA to `backend/static`.

2. Install backend dependencies:

```bash
cd ../backend
python -m pip install -r requirements.txt
```

3. Set environment variables:

```env
APP_ENV=production
APP_DEBUG=false
API_REQUIRE_KEY=true
API_KEY=<long-random-demo-key>
ENABLE_DETECTION_WORKER=false
DB_FALLBACK_SQLITE=false
CORS_ORIGINS=https://your-domain.example
```

4. Start the ASGI server:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

The backend serves:

- API routes under `/api`
- WebSocket route `/ws/stream/{camera_id}`
- Uploaded/generated files under `/storage`
- SPA assets under `/assets`
- SPA fallback for non-API routes

## Render Free Demo Notes

Render Free can run Python web services and static sites, but treat it as a demo
target only for this ALPR app. Render documents important Free limitations:
services spin down after idle time, local filesystem changes are lost on
redeploy/restart/spin-down, and Free web services do not support persistent
disks. See [Render Free docs](https://render.com/docs/free).

Practical defaults for Render Free:

- Keep `ENABLE_DETECTION_WORKER=false`.
- Do not rely on SQLite or local `/storage` for persistent data.
- Use external database/storage for anything beyond a short demo.
- Expect cold starts after idle periods, including WebSocket reconnects.

## cPanel Fallback

Shared cPanel is acceptable for serving the built static frontend and, if
available, MySQL. It should not be treated as a complete host for this FastAPI
app when the environment only supports Passenger WSGI.

`backend/passenger_wsgi.py` is now documented as an HTTP compatibility fallback.
Full functionality needs ASGI:

- WebSocket live monitor
- FastAPI lifespan service initialization
- Optional background DetectionWorker

If cPanel cannot run ASGI, deploy the backend to an ASGI host and point the SPA
to it with:

```env
VITE_API_BASE_URL=https://api.your-domain.example
VITE_WS_BASE_URL=wss://api.your-domain.example
VITE_API_KEY=<same-demo-key>
```

## Other Free-Tier References

- Koyeb documents one free web service with 512MB RAM, 0.1 vCPU, and 2GB SSD,
  which is likely too small for YOLO plus OCR. See
  [Koyeb pricing FAQ](https://www.koyeb.com/docs/faqs/pricing).
- Railway documents a free trial for new users with up to 30 days and a one-time
  $5 grant, then a Free plan with a small non-rollover monthly credit. Treat it
  as a limited demo budget, not production capacity. See
  [Railway free trial](https://docs.railway.com/pricing/free-trial).
- Fly.io documents that there is no free account/free tier and free allowances do
  not cap billing. See [Fly cost management](https://fly.io/docs/about/cost-management/).

## Verification Checklist

Before handing over a demo deployment:

```bash
cd backend
python -m pytest

cd ../frontend
npm run build
```

Manual checks:

- `/health` returns loaded/unavailable ML status accurately.
- Upload detection returns `detections`, `annotated_image_url`, `image_width`,
  `image_height`, `bbox`, and `bbox_norm`.
- Dashboard uses `ocr_accuracy_pct`, `avg_confidence_pct`, and by-source data.
- WebSocket URL includes `?api_key=...` when API key is configured.
- Live monitor overlays use `bbox_norm` and align with the streamed frame.
