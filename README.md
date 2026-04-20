# ALPR Indonesia — Backend

## Quick Start

### 1. Setup Environment

```bash
cd alpr-indonesia/backend

# Copy env template
cp ../.env.example ../.env
# Edit .env — set DB_HOST, DB_NAME, DB_USER, DB_PASSWORD

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Backend

```bash
cd alpr-indonesia/backend
python main.py
# OR
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API docs: http://localhost:8000/docs  
Health check: http://localhost:8000/health

---

## API Endpoints (Fase 1 + 2)

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Liveness probe |
| **Detection** | | |
| POST | /api/detect | Upload image/video → ALPR pipeline |
| GET | /api/detections | Paginated history with filters |
| GET | /api/detections/{id} | Single detection detail |
| **Cameras** | | |
| GET | /api/cameras | List all cameras |
| POST | /api/cameras | Register new camera |
| GET | /api/cameras/{id} | Camera detail |
| PUT | /api/cameras/{id} | Update camera config |
| DELETE | /api/cameras/{id} | Deactivate camera |
| POST | /api/cameras/{id}/test | Test RTSP connection |
| **Vehicles** | | |
| GET | /api/vehicles | List/search vehicles |
| POST | /api/vehicles | Add vehicle to DB |
| GET | /api/vehicles/lookup/{plate} | Quick plate lookup |
| GET | /api/vehicles/{id} | Vehicle detail |
| PUT | /api/vehicles/{id} | Update vehicle |
| DELETE | /api/vehicles/{id} | Remove vehicle |
| POST | /api/vehicles/{id}/flag | Flag vehicle |
| **Stats** | | |
| GET | /api/stats | Dashboard summary |
| GET | /api/stats/chart | Daily chart data |
| GET | /api/stats/by-region | Breakdown by region |
| GET | /api/stats/by-camera | Per-camera counts |
| GET | /api/stats/by-source | By source type |
| GET | /api/stats/alerts | Recent watchlist hits |
| **Export** | | |
| GET | /api/export/csv | Download CSV |
| GET | /api/export/json | Download JSON |
| GET | /api/export/status | Export availability |
| **Stream** | | |
| WS | /ws/stream/{camera_id} | Live WebSocket stream |
| GET | /api/stream/status | Active streams list |

---

## Test Commands

### Health Check
```bash
curl http://localhost:8000/health
```

### Upload Image Detection
```bash
curl -X POST http://localhost:8000/api/detect \
  -F "file=@/path/to/car.jpg" \
  -F "camera_id=1"
```

### Register Camera
```bash
curl -X POST http://localhost:8000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{"name":"Kamera Depan","location":"Pintu Utama","rtsp_url":"rtsp://admin:pass@192.168.1.100/stream","is_active":true,"stream_fps":5}'
```

### Dashboard Stats
```bash
curl "http://localhost:8000/api/stats?days=7"
```

### Export CSV
```bash
curl "http://localhost:8000/api/export/csv?days=7&status=valid" -o detections.csv
```

### WebSocket Test (wscat)
```bash
npm install -g wscat
wscat -c "ws://localhost:8000/ws/stream/1?source_override=0"
```

---

## Expected Response Format

```json
{
  "success": true,
  "data": { ... },
  "message": "Detection completed"
}
```

Error format:
```json
{
  "success": false,
  "data": null,
  "message": "Error description"
}
```
