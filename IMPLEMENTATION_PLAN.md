# ALPR Indonesia — Implementation Plan
**Automatic License Plate Recognition System**
Dokumen ini adalah panduan lengkap untuk AI Agent (Claude via Antigravity) dalam membangun sistem ALPR Indonesia dari nol.

---

## 1. RINGKASAN PROYEK

**Nama Proyek:** ALPR Indonesia — Automatic License Plate Recognition
**Tujuan:** Sistem deteksi dan pembacaan plat nomor kendaraan Indonesia secara real-time dari feed CCTV atau upload gambar/video, ditampilkan dalam dashboard web modern.
**Target Deployment:** Shared Hosting cPanel (Python App + subdomain untuk backend) atau VPS minimal
**Audiens:** Portfolio AI Engineer — menunjukkan kemampuan Computer Vision, OCR, backend API, dan frontend dashboard

---

## 2. KEPUTUSAN STACK TEKNOLOGI

### 2.1 Rekomendasi Stack (Optimized untuk cPanel Shared Hosting)

Karena Gimm familiar dengan Laravel + Vue.js TETAPI target deployment adalah cPanel shared hosting yang tidak support Docker/systemd, berikut adalah stack yang direkomendasikan:

| Layer | Teknologi | Alasan |
|---|---|---|
| Backend API | **FastAPI (Python)** | Native Python App support di cPanel, async, modern |
| ML Engine | **YOLOv8n (Ultralytics)** | Model nano = ringan, cukup akurat untuk plat |
| OCR Engine | **PaddleOCR** | Akurasi tinggi untuk karakter Latin, support GPU/CPU |
| Database | **MySQL** | Native support cPanel, tidak perlu instalasi tambahan |
| Cache/Queue | **Redis** (opsional) | Jika VPS; ganti dengan file-based queue di shared hosting |
| Frontend | **Vue.js 3 + Vite (SPA)** | Build static, host di public_html cPanel |
| HTTP Client | **Axios** | Komunikasi frontend ke FastAPI |
| Styling | **Tailwind CSS** | Utility-first, build time kecil |
| Realtime | **WebSocket (FastAPI native)** | Live feed tanpa library tambahan |

### 2.2 Kenapa BUKAN Laravel + Vue Full-Stack di cPanel?

- Laravel membutuhkan PHP + Composer, tidak bisa jalankan proses Python ML secara langsung
- YOLOv8 dan PaddleOCR adalah library Python — harus ada Python environment
- Arsitektur yang paling masuk akal: **FastAPI sebagai backend tunggal**, Vue.js sebagai SPA static di subdomain terpisah
- Alternatif: Laravel sebagai "proxy/wrapper" yang call FastAPI via HTTP — tapi menambah kompleksitas tidak perlu

### 2.3 Opsi Stack Alternatif (Jika Ada VPS/Docker)

| Layer | Teknologi |
|---|---|
| Backend | FastAPI + Uvicorn + Nginx |
| Database | PostgreSQL |
| Cache | Redis |
| Queue | Celery + Redis |
| Deploy | Docker Compose |
| Frontend | Next.js 14 (SSR) atau Vue.js 3 (SPA) |

---

## 3. ARSITEKTUR SISTEM

### 3.1 Overview Arsitektur

```
[BROWSER / DASHBOARD]
        |
        | HTTP/WebSocket
        v
[FastAPI Backend — Python App cPanel]
        |
   +---------+----------+----------+
   |         |          |          |
[YOLOv8] [PaddleOCR] [MySQL DB] [File Storage]
   |         |
   +----+----+
        |
   [Plate Validator]
   [Region Mapper]
```

### 3.2 Alur Data Lengkap

**A. Mode Upload Gambar/Video:**
1. User upload file via frontend (Vue.js)
2. Frontend POST ke `/api/detect` dengan multipart/form-data
3. FastAPI terima file, simpan sementara ke `storage/temp/`
4. YOLOv8 detect bounding box area plat nomor di gambar
5. Crop setiap bounding box yang ditemukan
6. Preprocessing: grayscale, denoise, sharpen crop hasil
7. PaddleOCR baca teks dari crop
8. Plate Validator: regex validation format plat Indonesia
9. Region Mapper: map prefix plat ke wilayah (B = Jakarta, D = Bandung, dll)
10. Simpan hasil ke MySQL (tabel `detections`)
11. Return JSON response ke frontend
12. Frontend render hasil di dashboard

**B. Mode Live Stream CCTV (WebSocket):**
1. Frontend buka WebSocket connection ke `/ws/stream/{camera_id}`
2. Backend start capture dari RTSP URL yang dikonfigurasi
3. Setiap frame diproses oleh YOLOv8 (skip frame jika processing masih berjalan)
4. Hasil deteksi dikirim via WebSocket sebagai JSON + base64 frame annotated
5. Frontend render frame + overlay bounding box secara realtime
6. Setiap deteksi baru disimpan ke database

**C. Mode Upload Video:**
1. User upload file video (.mp4, .avi, .mov)
2. Backend ekstrak frame setiap N detik (configurable)
3. Proses setiap frame seperti mode gambar
4. Simpan semua hasil sebagai batch ke database
5. Return summary: total frame, total plat terdeteksi, unique plates

### 3.3 Komponen Backend

```
FastAPI App
├── /api/detect          POST  - Deteksi dari gambar/video upload
├── /api/detections      GET   - List semua deteksi (dengan filter)
├── /api/detections/{id} GET   - Detail satu deteksi
├── /api/cameras         GET   - List kamera yang terdaftar
├── /api/cameras         POST  - Tambah kamera baru
├── /api/vehicles        GET   - Lookup database kendaraan
├── /api/vehicles/{plate}GET   - Cari kendaraan by plat
├── /api/stats           GET   - Statistik dashboard
├── /api/export/csv      GET   - Export hasil ke CSV
└── /ws/stream/{cam_id}  WS    - Live stream WebSocket
```

---

## 4. STRUKTUR FOLDER LENGKAP

```
alpr-indonesia/
│
├── backend/                        # FastAPI Python Application
│   ├── main.py                     # Entry point FastAPI app
│   ├── config.py                   # Konfigurasi (DB, paths, model)
│   ├── database.py                 # SQLAlchemy setup + koneksi MySQL
│   ├── requirements.txt            # Semua dependency Python
│   ├── passenger_wsgi.py           # Entry point untuk cPanel Python App
│   │
│   ├── routers/                    # FastAPI routers (group endpoint)
│   │   ├── __init__.py
│   │   ├── detection.py            # POST /api/detect, GET /api/detections
│   │   ├── cameras.py              # CRUD kamera
│   │   ├── vehicles.py             # Lookup kendaraan
│   │   ├── stats.py                # Statistik dashboard
│   │   ├── export.py               # Export CSV/JSON
│   │   └── stream.py               # WebSocket live stream
│   │
│   ├── services/                   # Business logic layer
│   │   ├── __init__.py
│   │   ├── yolo_service.py         # YOLOv8 inference, crop, annotate
│   │   ├── ocr_service.py          # PaddleOCR read text dari crop
│   │   ├── plate_validator.py      # Regex validation + region mapping
│   │   ├── preprocessor.py         # OpenCV image enhancement
│   │   └── stream_service.py       # RTSP capture + frame processing
│   │
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── detection.py            # Model tabel detections
│   │   ├── camera.py               # Model tabel cameras
│   │   └── vehicle.py              # Model tabel vehicles (lookup)
│   │
│   ├── schemas/                    # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── detection.py
│   │   ├── camera.py
│   │   └── vehicle.py
│   │
│   ├── utils/                      # Helper functions
│   │   ├── __init__.py
│   │   ├── image_utils.py          # Konversi gambar, resize, annotate
│   │   └── response.py             # Standard API response format
│   │
│   ├── ml_models/                  # Folder penyimpanan model files
│   │   ├── yolov8n.pt              # YOLOv8 nano pretrained (default)
│   │   └── yolov8n_plate.pt        # YOLOv8 fine-tuned plat (setelah training)
│   │
│   ├── storage/                    # File storage
│   │   ├── temp/                   # Upload sementara (auto-clean)
│   │   ├── results/                # Gambar hasil annotasi
│   │   └── exports/                # File CSV/JSON export
│   │
│   ├── migrations/                 # Alembic DB migrations
│   │   └── versions/
│   │
│   └── tests/                      # Unit tests
│       ├── test_yolo.py
│       ├── test_ocr.py
│       └── test_validator.py
│
├── frontend/                       # Vue.js 3 SPA
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── tailwind.config.js
│   │
│   ├── src/
│   │   ├── main.js                 # Vue app entry point
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.js            # Vue Router konfigurasi
│   │   │
│   │   ├── stores/                 # Pinia state management
│   │   │   ├── detection.js        # State deteksi
│   │   │   ├── camera.js           # State kamera
│   │   │   └── stats.js            # State statistik
│   │   │
│   │   ├── views/                  # Halaman utama
│   │   │   ├── DashboardView.vue   # Halaman dashboard utama
│   │   │   ├── LiveMonitorView.vue # Live CCTV monitoring
│   │   │   ├── HistoryView.vue     # Riwayat deteksi
│   │   │   ├── VehiclesView.vue    # Database kendaraan
│   │   │   └── SettingsView.vue    # Pengaturan sistem
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── TopNav.vue
│   │   │   │   ├── Sidebar.vue
│   │   │   │   └── MainLayout.vue
│   │   │   │
│   │   │   ├── dashboard/
│   │   │   │   ├── MetricCard.vue
│   │   │   │   ├── DetectionChart.vue
│   │   │   │   └── SourceBreakdown.vue
│   │   │   │
│   │   │   ├── monitor/
│   │   │   │   ├── LiveFeed.vue        # Canvas/img dengan bounding box overlay
│   │   │   │   ├── PlateResult.vue     # Display hasil OCR
│   │   │   │   └── DetectionLog.vue    # Tabel deteksi realtime
│   │   │   │
│   │   │   └── shared/
│   │   │       ├── PlateBadge.vue
│   │   │       ├── StatusBadge.vue
│   │   │       └── ConfidenceBar.vue
│   │   │
│   │   ├── composables/
│   │   │   ├── useWebSocket.js     # WebSocket connection management
│   │   │   ├── useDetection.js     # Detection API calls
│   │   │   └── useStats.js         # Stats API calls
│   │   │
│   │   ├── services/
│   │   │   └── api.js              # Axios instance + semua API calls
│   │   │
│   │   └── assets/
│   │       └── styles/
│   │           └── main.css        # Tailwind directives
│   │
│   └── dist/                       # Build output (deploy ke public_html)
│
├── ml/                             # Machine Learning scripts
│   ├── train_yolo.py               # Script training YOLOv8 custom
│   ├── evaluate_model.py           # Evaluasi performa model
│   ├── download_dataset.py         # Download dataset dari Roboflow
│   ├── test_inference.py           # Test inferensi dengan gambar sampel
│   └── dataset/
│       ├── images/
│       │   ├── train/
│       │   └── val/
│       └── labels/
│           ├── train/
│           └── val/
│
├── docs/                           # Dokumentasi
│   ├── IMPLEMENTATION_PLAN.md      # File ini
│   ├── API_DOCS.md
│   └── DEPLOYMENT_GUIDE.md
│
├── .env.example                    # Template environment variables
├── .gitignore
└── README.md
```

---

## 5. DETAIL DATABASE SCHEMA

### Tabel: `detections`
```sql
CREATE TABLE detections (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    camera_id       BIGINT NULL,
    plate_text      VARCHAR(20) NOT NULL,
    plate_raw       VARCHAR(20),           -- OCR raw sebelum cleaning
    confidence      FLOAT,                 -- Confidence score YOLOv8 (0-1)
    ocr_confidence  FLOAT,                 -- Confidence score OCR (0-1)
    region          VARCHAR(100),          -- Wilayah (misal: DKI Jakarta)
    region_code     VARCHAR(5),            -- Kode plat (B, D, L, dll)
    vehicle_type    VARCHAR(50),           -- Jenis kendaraan jika diketahui
    image_path      VARCHAR(255),          -- Path gambar annotasi
    crop_path       VARCHAR(255),          -- Path crop area plat
    source_type     ENUM('upload','stream','video_batch'),
    status          ENUM('valid','invalid','watchlist','ocr_failed'),
    raw_frame_ts    TIMESTAMP NULL,        -- Timestamp frame dari stream
    detected_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE SET NULL,
    INDEX idx_plate_text (plate_text),
    INDEX idx_detected_at (detected_at),
    INDEX idx_status (status)
);
```

### Tabel: `cameras`
```sql
CREATE TABLE cameras (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    location    VARCHAR(200),
    rtsp_url    TEXT,                      -- RTSP stream URL (encrypted)
    is_active   BOOLEAN DEFAULT TRUE,
    stream_fps  INT DEFAULT 5,             -- Frame per second to process
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tabel: `vehicles` (lookup database)
```sql
CREATE TABLE vehicles (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    plate_text      VARCHAR(20) UNIQUE NOT NULL,
    owner_name      VARCHAR(100),
    vehicle_type    VARCHAR(50),
    brand           VARCHAR(50),
    color           VARCHAR(30),
    year            INT,
    status          ENUM('normal','watchlist','stolen','expired'),
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_plate_text (plate_text),
    INDEX idx_status (status)
);
```

---

## 6. DETAIL MODEL DAN YOLO

### 6.1 Model YOLOv8 — Tahap Penggunaan

**Tahap 1 — Gunakan Pretrained (Cepat, tanpa training):**
- Unduh model: `yolov8n.pt` (nano, 6MB) dari ultralytics
- Pretrained COCO dataset sudah bisa detect objek umum termasuk mobil/motor
- Untuk deteksi AREA plat: model perlu fine-tune karena COCO tidak ada class "license plate"
- Cara cepat: jalankan YOLOv8 untuk detect kendaraan dulu, lalu crop area bawah/depan kendaraan, baru OCR

**Tahap 2 — Fine-tune untuk Deteksi Plat (Recommended):**
- Dataset: Download dari Roboflow Universe (search: "license plate indonesia")
- Format dataset: YOLO format (file .txt per gambar berisi class + bbox coordinates)
- Training command:
```python
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
model.train(
    data='dataset/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    name='yolov8n_plate_indonesia',
    patience=20,
    save=True
)
```
- Hasil training: `runs/detect/yolov8n_plate_indonesia/weights/best.pt`
- Salin ke: `backend/ml_models/yolov8n_plate.pt`

### 6.2 Konfigurasi file `data.yaml`
```yaml
path: ./dataset
train: images/train
val: images/val
nc: 1
names: ['license_plate']
```

### 6.3 YOLOv8 Inference di Backend (`yolo_service.py`)
```python
from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path

class YOLOService:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)
        self.conf_threshold = 0.45
    
    def detect(self, image_path: str) -> list[dict]:
        """
        Deteksi plat nomor dalam gambar.
        Return list of dicts: {bbox, confidence, crop_path}
        """
        img = cv2.imread(image_path)
        results = self.model(img, conf=self.conf_threshold)
        detections = []
        
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                crop = img[y1:y2, x1:x2]
                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": conf,
                    "crop": crop
                })
        return detections
    
    def annotate(self, image_path: str, detections: list, output_path: str):
        """Gambar bounding box di gambar asli, simpan ke output_path."""
        img = cv2.imread(image_path)
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{det.get('plate_text', '')} {det['confidence']:.2f}"
            cv2.putText(img, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imwrite(output_path, img)
```

### 6.4 PaddleOCR Setup (`ocr_service.py`)
```python
from paddleocr import PaddleOCR
import cv2
import numpy as np

class OCRService:
    def __init__(self):
        # use_angle_cls=True untuk handle plat miring
        # lang='en' karena plat Indonesia pakai huruf Latin
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    
    def read_plate(self, crop: np.ndarray) -> dict:
        """
        Baca teks dari crop gambar plat.
        Return: {text, confidence}
        """
        # Preprocessing sebelum OCR
        enhanced = self._enhance(crop)
        result = self.ocr.ocr(enhanced, cls=True)
        
        if not result or not result[0]:
            return {"text": "", "confidence": 0.0}
        
        # Ambil text dengan confidence tertinggi
        texts = []
        for line in result[0]:
            text, conf = line[1]
            texts.append((text, conf))
        
        if not texts:
            return {"text": "", "confidence": 0.0}
        
        best = max(texts, key=lambda x: x[1])
        # Cleaning: hapus spasi ekstra, uppercase
        cleaned = best[0].upper().replace(".", "").strip()
        return {"text": cleaned, "confidence": float(best[1])}
    
    def _enhance(self, img: np.ndarray) -> np.ndarray:
        """Preprocessing: resize, grayscale, denoise, sharpen."""
        # Resize jika terlalu kecil
        h, w = img.shape[:2]
        if w < 200:
            scale = 200 / w
            img = cv2.resize(img, (int(w * scale), int(h * scale)),
                             interpolation=cv2.INTER_CUBIC)
        # Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        # Sharpen
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpened = cv2.filter2D(denoised, -1, kernel)
        # Convert back to BGR untuk PaddleOCR
        return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)
```

---

## 7. LOGIC VALIDASI PLAT INDONESIA

### 7.1 Format Plat Indonesia
```
[Kode Wilayah 1-2 huruf] [Nomor 1-4 digit] [Seri 1-3 huruf]
Contoh: B 1234 NVA, D 5678 AB, L 9900 CD
Khusus:  TNI 1234, POLRI 5678, CD 123 (Korps Diplomatik)
```

### 7.2 Implementasi Validator (`plate_validator.py`)
```python
import re

REGION_MAP = {
    "A": "Banten", "B": "DKI Jakarta", "BE": "Lampung",
    "BG": "Sumatera Selatan", "BH": "Jambi", "BK": "Sumatera Utara",
    "BL": "Aceh", "BM": "Riau", "BN": "Bangka Belitung",
    "BP": "Kepulauan Riau", "D": "Bandung", "DA": "Kalimantan Selatan",
    "DB": "Sulawesi Utara", "DC": "Sulawesi Barat", "DD": "Sulawesi Selatan",
    "DE": "Maluku", "DG": "Sulawesi Selatan", "DH": "NTT",
    "DK": "Bali", "DL": "Sulawesi Utara", "DM": "Gorontalo",
    "DN": "Sulawesi Tengah", "DT": "Sulawesi Tenggara", "E": "Cirebon",
    "EA": "NTB", "EB": "NTT", "ED": "NTT", "F": "Bogor",
    "G": "Pekalongan", "H": "Semarang", "K": "Pati",
    "KB": "Kalimantan Barat", "KH": "Kalimantan Tengah",
    "KT": "Kalimantan Timur", "KU": "Kalimantan Utara",
    "L": "Surabaya", "M": "Madura", "N": "Malang",
    "P": "Besuki (Jawa Timur)", "PA": "Papua", "PB": "Papua Barat",
    "R": "Banyumas", "S": "Bojonegoro", "T": "Karawang",
    "W": "Gresik", "Z": "Tasikmalaya",
}

PLATE_PATTERN = re.compile(
    r'^([A-Z]{1,2})\s?(\d{1,4})\s?([A-Z]{1,3})$'
)
SPECIAL_PATTERN = re.compile(
    r'^(TNI|POLRI|CD|RF|RFH|RFS|RFP|RFD|RFL)\s?\d+'
)

def validate_plate(raw_text: str) -> dict:
    text = raw_text.upper().strip()
    # Hapus karakter non-alfanumerik kecuali spasi
    text = re.sub(r'[^A-Z0-9\s]', '', text)
    
    # Cek pola khusus
    if SPECIAL_PATTERN.match(text):
        return {"plate": text, "valid": True, "status": "special",
                "region": "Kendaraan Dinas", "region_code": text.split()[0]}
    
    match = PLATE_PATTERN.match(text)
    if not match:
        return {"plate": text, "valid": False, "status": "invalid",
                "region": "Tidak dikenal", "region_code": ""}
    
    code = match.group(1)
    region = REGION_MAP.get(code, "Wilayah tidak terdaftar")
    
    # Format ulang dengan spasi standar
    formatted = f"{match.group(1)} {match.group(2)} {match.group(3)}"
    
    return {
        "plate": formatted,
        "plate_raw": raw_text,
        "valid": True,
        "status": "valid",
        "region": region,
        "region_code": code
    }
```

---

## 8. LIVE STREAM — INTEGRASI CCTV

### 8.1 Pilihan Sumber Stream (Gratis/Open Source)

| Sumber | Protokol | Keterangan |
|---|---|---|
| IP Camera fisik | RTSP | Format: `rtsp://user:pass@ip:554/stream` |
| MediaMTX (simulasi) | RTSP | Push video file sebagai stream RTSP |
| Webcam laptop | WebRTC/OpenCV | Gunakan index device (0 = default cam) |
| Video file lokal | File path | OpenCV baca file MP4/AVI |
| YouTube Live | HLS/RTMP | Melalui yt-dlp (khusus demo) |

### 8.2 MediaMTX Setup (Open Source, Gratis)
```bash
# Download dari: https://github.com/bluenviron/mediamtx/releases
# Jalankan server RTSP lokal
./mediamtx

# Push video file sebagai stream RTSP (gunakan ffmpeg)
ffmpeg -re -stream_loop -1 -i sample_traffic.mp4 \
  -c copy -f rtsp rtsp://localhost:8554/cctv1

# URL yang dipakai di aplikasi:
# rtsp://localhost:8554/cctv1
```

### 8.3 WebSocket Stream Handler (`stream_service.py`)
```python
import asyncio
import cv2
import base64
from fastapi import WebSocket

class StreamService:
    def __init__(self, yolo_service, ocr_service):
        self.yolo = yolo_service
        self.ocr = ocr_service
        self.active_streams = {}
    
    async def start_stream(self, websocket: WebSocket, camera_id: int, rtsp_url: str):
        await websocket.accept()
        cap = cv2.VideoCapture(rtsp_url)
        frame_count = 0
        process_every = 5  # Proses setiap 5 frame (hemat resource)
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                result_data = {"frame": None, "detections": []}
                
                # Encode frame untuk dikirim ke frontend
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                frame_b64 = base64.b64encode(buffer).decode('utf-8')
                result_data["frame"] = frame_b64
                
                # Hanya proses deteksi setiap N frame
                if frame_count % process_every == 0:
                    detections = self.yolo.detect_from_frame(frame)
                    for det in detections:
                        crop = frame[det['bbox'][1]:det['bbox'][3],
                                     det['bbox'][0]:det['bbox'][2]]
                        ocr_result = self.ocr.read_plate(crop)
                        det['plate_text'] = ocr_result['text']
                        det['ocr_confidence'] = ocr_result['confidence']
                    result_data["detections"] = detections
                
                await websocket.send_json(result_data)
                await asyncio.sleep(0.033)  # ~30fps kirim frame
                
        except Exception as e:
            print(f"Stream error: {e}")
        finally:
            cap.release()
            await websocket.close()
```

---

## 9. REQUIREMENTS.TXT LENGKAP

```
# Web Framework
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-multipart==0.0.9

# Database
sqlalchemy==2.0.30
pymysql==1.1.0
alembic==1.13.1

# Machine Learning
ultralytics==8.2.0         # YOLOv8
paddlepaddle==2.6.1        # PaddleOCR backend
paddleocr==2.7.3

# Image Processing
opencv-python-headless==4.9.0.80   # headless: tanpa GUI dependency
numpy==1.26.4
Pillow==10.3.0

# Utilities
python-dotenv==1.0.1
pydantic-settings==2.2.1
aiofiles==23.2.1

# Export
pandas==2.2.2

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

---

## 10. ENVIRONMENT VARIABLES (.env.example)

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=alpr_db
DB_USER=root
DB_PASSWORD=secret

# App
APP_ENV=development
APP_DEBUG=true
API_SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:5173,http://yourdomain.com

# ML Models
YOLO_MODEL_PATH=ml_models/yolov8n_plate.pt
YOLO_CONFIDENCE=0.45
OCR_LANGUAGE=en

# Storage
STORAGE_PATH=storage
MAX_UPLOAD_SIZE_MB=50
TEMP_FILE_TTL_HOURS=24

# Stream
DEFAULT_STREAM_FPS=5
PROCESS_EVERY_N_FRAMES=5

# RTSP Cameras (JSON array)
# CAMERAS=[{"id":1,"name":"Pintu Masuk","rtsp_url":"rtsp://..."}]
```

---

## 11. DEPLOY KE CPANEL SHARED HOSTING

### 11.1 Backend (Python App)
1. Buka cPanel → "Setup Python App"
2. Python version: 3.10 atau 3.11
3. Application root: `/home/username/alpr_backend`
4. Application URL: `api.yourdomain.com` (subdomain)
5. Application startup file: `passenger_wsgi.py`
6. Upload semua file backend via File Manager atau Git
7. Install dependencies via cPanel terminal: `pip install -r requirements.txt`

### 11.2 File `passenger_wsgi.py`
```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Aktifkan virtual environment cPanel
VENV_PATH = os.path.join(os.path.dirname(__file__), 'venv')
if os.path.exists(VENV_PATH):
    activate = os.path.join(VENV_PATH, 'bin', 'activate_this.py')
    exec(open(activate).read(), {'__file__': activate})

from main import app as application
```

### 11.3 Frontend (Static SPA)
1. Build Vue.js: `npm run build` → output ke `dist/`
2. Upload isi folder `dist/` ke `public_html/` atau subdomain folder
3. Tambah file `.htaccess` untuk Vue Router history mode:
```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>
```

---

## 12. INSTRUKSI UNTUK AI AGENT (ANTIGRAVITY)

### Urutan Pengerjaan yang Disarankan:

**Fase 1 — Backend Core (Prioritas Tinggi)**
1. Buat struktur folder backend sesuai Section 4
2. Setup `main.py` dengan FastAPI, CORS, routing
3. Setup `database.py` dengan SQLAlchemy + MySQL
4. Buat semua model SQLAlchemy (Section 5)
5. Implementasi `yolo_service.py` (Section 6.3)
6. Implementasi `ocr_service.py` (Section 6.4)
7. Implementasi `plate_validator.py` (Section 7.2)
8. Buat router `detection.py` — endpoint POST /api/detect
9. Test dengan gambar statis

**Fase 2 — Backend Extended**
10. Buat router `cameras.py`, `vehicles.py`, `stats.py`, `export.py`
11. Implementasi `stream_service.py` + router `stream.py` (WebSocket)
12. Setup Alembic migrations
13. Buat `passenger_wsgi.py` untuk cPanel

**Fase 3 — Frontend**
14. Setup Vue.js 3 + Vite + Tailwind CSS + Pinia + Vue Router
15. Buat layout komponen (TopNav, Sidebar, MainLayout)
16. Buat DashboardView dengan MetricCard + DetectionChart
17. Buat LiveMonitorView dengan WebSocket + canvas overlay
18. Buat HistoryView dengan tabel + filter + export
19. Buat SettingsView untuk manajemen kamera
20. Konfigurasi `api.js` dengan Axios pointing ke FastAPI URL

**Fase 4 — Integrasi & Polish**
21. Test end-to-end: upload gambar → hasil tampil di dashboard
22. Test WebSocket: stream RTSP → tampil di LiveMonitor
23. Test export CSV
24. Tambah loading states, error handling di frontend
25. Finalize `.htaccess` dan konfigurasi CORS untuk production

### Catatan Penting untuk Agent:
- Selalu gunakan async/await untuk semua endpoint FastAPI
- Semua response gunakan format standard: `{"success": true, "data": {...}, "message": "..."}`
- Upload file ke `storage/temp/` lalu proses, jangan proses langsung dari memory untuk file besar
- WebSocket: kirim frame sebagai base64 JPEG (quality 60) untuk hemat bandwidth
- YOLOv8: gunakan `yolov8n.pt` (nano) secara default untuk kecepatan, bisa diganti `yolov8s.pt` jika akurasi kurang
- PaddleOCR: inisialisasi SATU instance saat startup (lambat jika diinisialisasi per request)
- Semua path file: gunakan `pathlib.Path` bukan string concatenation
