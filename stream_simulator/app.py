"""
stream_simulator/app.py
Video-to-Live-Stream Simulator for ALPR Indonesia.
"""

import asyncio, json, logging, os, shutil, subprocess, sys, uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response, FileResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
STREAMS_DIR = BASE_DIR / "streams"
TOOLS_DIR = BASE_DIR / "tools"
TEMPLATES_DIR = BASE_DIR / "templates"
DB_FILE = BASE_DIR / "streams_db.json"

FFMPEG_BIN = str(TOOLS_DIR / "ffmpeg.exe") if sys.platform == "win32" else "ffmpeg"
FFPROBE_BIN = str(TOOLS_DIR / "ffprobe.exe") if sys.platform == "win32" else "ffprobe"

for d in [UPLOADS_DIR, STREAMS_DIR, TEMPLATES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("stream_simulator")


# --- JSON DB ---
def _load_db():
    if DB_FILE.exists():
        try: return json.loads(DB_FILE.read_text(encoding="utf-8"))
        except: pass
    return {"streams": {}}

def _save_db(db):
    DB_FILE.write_text(json.dumps(db, indent=2, default=str), encoding="utf-8")


# --- FFmpeg ---
_ffmpeg_processes = {}

def _get_video_info(video_path):
    try:
        cmd = [FFPROBE_BIN, "-v", "quiet", "-print_format", "json",
               "-show_format", "-show_streams", str(video_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        info = json.loads(result.stdout)
        vs = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
        fmt = info.get("format", {})
        dur = float(fmt.get("duration", 0))
        fps_str = vs.get("r_frame_rate", "25/1")
        try:
            n, d = fps_str.split("/"); fps = round(int(n) / int(d), 2)
        except: fps = 25.0
        return {"duration": round(dur, 2), "width": int(vs.get("width", 0)),
                "height": int(vs.get("height", 0)), "fps": fps,
                "codec": vs.get("codec_name", "unknown"),
                "size_mb": round(os.path.getsize(video_path) / 1024 / 1024, 2)}
    except Exception as e:
        logger.warning("ffprobe failed: %s", e)
        return {"duration": 0, "width": 0, "height": 0, "fps": 25, "codec": "unknown", "size_mb": 0}


def _start_hls_stream(stream_id, video_path, stream_dir):
    stream_dir.mkdir(parents=True, exist_ok=True)
    playlist = stream_dir / "index.m3u8"
    log_file = stream_dir / "ffmpeg.log"

    cmd = [
        FFMPEG_BIN, "-y",
        "-re",
        "-stream_loop", "-1",
        "-i", str(video_path),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-g", "30",
        "-sc_threshold", "0",
        "-b:v", "2500k",
        "-maxrate", "3000k",
        "-bufsize", "6000k",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
        "-an",
        "-f", "hls",
        "-hls_time", "2",
        "-hls_list_size", "5",
        "-hls_flags", "delete_segments+append_list",
        "-hls_segment_filename", str(stream_dir / "seg_%05d.ts"),
        str(playlist),
    ]
    logger.info("Starting HLS stream: %s", stream_id)
    cf = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    stderr_fh = open(str(log_file), "w")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=stderr_fh, creationflags=cf)
    _ffmpeg_processes[stream_id] = proc
    return proc


def _stop_hls_stream(stream_id):
    proc = _ffmpeg_processes.pop(stream_id, None)
    if proc and proc.poll() is None:
        try: proc.terminate(); proc.wait(timeout=5)
        except: proc.kill()
        logger.info("Stopped stream: %s", stream_id)
        return True
    return False

def _is_stream_alive(stream_id):
    proc = _ffmpeg_processes.get(stream_id)
    return proc is not None and proc.poll() is None

def _do_start_stream(stream_id, db):
    stream = db["streams"][stream_id]
    video_path = UPLOADS_DIR / stream["video_file"]
    stream_dir = STREAMS_DIR / stream_id
    _start_hls_stream(stream_id, video_path, stream_dir)
    stream["status"] = "streaming"
    stream["started_at"] = datetime.now().isoformat()
    _save_db(db)

def _build_base_url(request):
    host = request.headers.get("host", "localhost:9000")
    scheme = "https" if request.url.scheme == "https" else "http"
    return f"{scheme}://{host}"


# --- Lifespan ---
@asynccontextmanager
async def lifespan(app):
    logger.info("=== Stream Simulator starting ===")
    db = _load_db()
    for sid, s in db["streams"].items():
        if s.get("status") == "streaming":
            vp = UPLOADS_DIR / s["video_file"]
            if vp.exists():
                logger.info("Auto-restarting stream: %s", sid)
                _do_start_stream(sid, db)
            else:
                s["status"] = "stopped"
    _save_db(db)
    yield
    logger.info("Shutting down all streams")
    for sid in list(_ffmpeg_processes.keys()):
        _stop_hls_stream(sid)


# --- App ---
app = FastAPI(title="ALPR Stream Simulator", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"],
                   expose_headers=["*"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# --- HLS file serving with proper CORS + content-type ---
@app.get("/streams/{stream_id}/{filename}")
async def serve_hls_file(stream_id: str, filename: str):
    """Serve HLS .m3u8 and .ts files with correct headers."""
    file_path = STREAMS_DIR / stream_id / filename
    if not file_path.exists() or not file_path.is_file():
        return Response(status_code=404, content="File not found")

    if filename.endswith(".m3u8"):
        content_type = "application/vnd.apple.mpegurl"
    elif filename.endswith(".ts"):
        content_type = "video/mp2t"
    else:
        content_type = "application/octet-stream"

    data = file_path.read_bytes()
    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


# --- Player page for a single stream ---
@app.get("/player/{stream_id}", response_class=HTMLResponse)
async def player_page(stream_id: str, request: Request):
    db = _load_db()
    stream = db["streams"].get(stream_id)
    if not stream:
        return HTMLResponse("<h1>Stream not found</h1>", status_code=404)
    base = _build_base_url(request)
    hls_url = f"{base}/streams/{stream_id}/index.m3u8"
    return templates.TemplateResponse("player.html", {
        "request": request, "stream": stream, "hls_url": hls_url
    })


# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...), name: str = Form(""),
                       auto_start: bool = Form(True)):
    ext = Path(file.filename or "video.mp4").suffix.lower()
    allowed = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}
    if ext not in allowed:
        return JSONResponse(status_code=422,
                            content={"success": False, "message": f"Format tidak didukung: {ext}"})

    stream_id = uuid.uuid4().hex[:12]
    video_filename = f"{stream_id}{ext}"
    video_path = UPLOADS_DIR / video_filename

    contents = await file.read()
    if len(contents) > 500 * 1024 * 1024:
        return JSONResponse(status_code=413,
                            content={"success": False, "message": "File terlalu besar (max 500MB)"})
    video_path.write_bytes(contents)

    video_info = _get_video_info(video_path)
    display_name = name.strip() or file.filename or f"Stream {stream_id}"

    stream_data = {
        "id": stream_id, "name": display_name, "video_file": video_filename,
        "video_info": video_info, "status": "stopped", "hls_url": None,
        "created_at": datetime.now().isoformat(), "started_at": None,
    }
    db = _load_db()
    db["streams"][stream_id] = stream_data
    _save_db(db)

    if auto_start:
        _do_start_stream(stream_id, db)

    return {"success": True, "data": db["streams"][stream_id], "message": "Video uploaded"}


@app.post("/api/streams/{stream_id}/start")
async def start_stream(stream_id: str):
    db = _load_db()
    stream = db["streams"].get(stream_id)
    if not stream:
        return JSONResponse(status_code=404, content={"success": False, "message": "Not found"})
    if _is_stream_alive(stream_id):
        return {"success": True, "data": stream, "message": "Already streaming"}
    _do_start_stream(stream_id, db)
    return {"success": True, "data": db["streams"][stream_id], "message": "Stream started"}


@app.post("/api/streams/{stream_id}/stop")
async def stop_stream(stream_id: str):
    db = _load_db()
    stream = db["streams"].get(stream_id)
    if not stream:
        return JSONResponse(status_code=404, content={"success": False, "message": "Not found"})
    _stop_hls_stream(stream_id)
    stream["status"] = "stopped"; stream["started_at"] = None
    _save_db(db)
    return {"success": True, "data": stream, "message": "Stream stopped"}


@app.post("/api/streams/{stream_id}/restart")
async def restart_stream(stream_id: str):
    db = _load_db()
    stream = db["streams"].get(stream_id)
    if not stream:
        return JSONResponse(status_code=404, content={"success": False, "message": "Not found"})
    _stop_hls_stream(stream_id)
    await asyncio.sleep(1)
    _do_start_stream(stream_id, db)
    return {"success": True, "data": db["streams"][stream_id], "message": "Stream restarted"}


@app.delete("/api/streams/{stream_id}")
async def delete_stream(stream_id: str):
    db = _load_db()
    stream = db["streams"].pop(stream_id, None)
    if not stream:
        return JSONResponse(status_code=404, content={"success": False, "message": "Not found"})
    _stop_hls_stream(stream_id)
    vp = UPLOADS_DIR / stream.get("video_file", "")
    if vp.exists(): vp.unlink(missing_ok=True)
    sd = STREAMS_DIR / stream_id
    if sd.exists(): shutil.rmtree(sd, ignore_errors=True)
    _save_db(db)
    return {"success": True, "message": "Stream deleted"}


@app.get("/api/streams")
async def list_streams(request: Request):
    db = _load_db()
    base = _build_base_url(request)
    streams = []
    for sid, s in db["streams"].items():
        alive = _is_stream_alive(sid)
        s["status"] = "streaming" if alive else "stopped"
        s["hls_url"] = f"{base}/streams/{sid}/index.m3u8" if alive else None
        s["player_url"] = f"{base}/player/{sid}" if alive else None
        streams.append(s)
    _save_db(db)
    return {"success": True, "data": streams}


@app.get("/api/streams/{stream_id}")
async def get_stream(stream_id: str, request: Request):
    db = _load_db()
    stream = db["streams"].get(stream_id)
    if not stream:
        return JSONResponse(status_code=404, content={"success": False, "message": "Not found"})
    base = _build_base_url(request)
    alive = _is_stream_alive(stream_id)
    stream["status"] = "streaming" if alive else "stopped"
    stream["hls_url"] = f"{base}/streams/{stream_id}/index.m3u8" if alive else None
    stream["player_url"] = f"{base}/player/{stream_id}" if alive else None
    _save_db(db)
    return {"success": True, "data": stream}


@app.post("/api/streams/{stream_id}/register-to-alpr")
async def register_to_alpr(stream_id: str, request: Request,
                           alpr_url: str = Form("http://localhost:8000"),
                           camera_name: str = Form(""), location: str = Form("Simulator")):
    import urllib.request, urllib.error
    db = _load_db()
    stream = db["streams"].get(stream_id)
    if not stream:
        return JSONResponse(status_code=404, content={"success": False, "message": "Not found"})
    if not _is_stream_alive(stream_id):
        return JSONResponse(status_code=400,
                            content={"success": False, "message": "Stream belum aktif"})

    base = _build_base_url(request)
    hls_url = f"{base}/streams/{stream_id}/index.m3u8"
    cam_name = camera_name.strip() or stream.get("name", f"Sim-{stream_id}")
    payload = json.dumps({"name": cam_name, "location": location.strip() or "Stream Simulator",
                          "rtsp_url": hls_url, "is_active": True, "stream_fps": 5}).encode()

    target = alpr_url.rstrip("/") + "/api/cameras"
    req = urllib.request.Request(target, data=payload,
                                headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
            return {"success": True, "data": {"alpr_response": body, "hls_url": hls_url},
                    "message": "Kamera berhasil didaftarkan ke ALPR"}
    except urllib.error.HTTPError as e:
        detail = e.read().decode() if e.fp else str(e)
        return JSONResponse(status_code=502,
                            content={"success": False, "message": f"ALPR API error: {detail}"})
    except Exception as e:
        return JSONResponse(status_code=502,
                            content={"success": False, "message": f"Gagal koneksi ke ALPR: {e}"})


if __name__ == "__main__":
    import uvicorn
    print()
    print("=" * 60)
    print("  ALPR Stream Simulator")
    print("  Upload video -> Generate HLS Live Stream")
    print("  Dashboard: http://localhost:9000")
    print("=" * 60)
    print()
    uvicorn.run("app:app", host="0.0.0.0", port=9000, reload=False, log_level="info")
