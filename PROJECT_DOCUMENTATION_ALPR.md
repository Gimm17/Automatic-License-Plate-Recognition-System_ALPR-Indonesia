# Dokumentasi Proyek: ALPR Indonesia (Automatic License Plate Recognition)

Dokumen ini berisi penjelasan menyeluruh mengenai proyek **ALPR Indonesia**, termasuk stack teknologi yang digunakan, arsitektur sistem, alur logika secara detail, serta model Machine Learning yang diimplementasikan.

---

## 1. Ringkasan Proyek
**ALPR Indonesia** adalah sebuah sistem cerdas (AI-powered) yang berfungsi untuk mendeteksi dan membaca plat nomor kendaraan Indonesia secara otomatis. Sistem ini mampu memproses gambar, video, maupun *live stream* (CCTV/RTSP) secara *real-time* dan menampilkan hasilnya melalui dashboard web yang modern.

**Tujuan Utama:**
- Mendeteksi plat nomor kendaraan secara akurat menggunakan Computer Vision.
- Mengekstrak teks dari plat nomor menggunakan sistem OCR (Optical Character Recognition).
- Memvalidasi format plat nomor sesuai standar Indonesia (termasuk kendaraan dinas/khusus) dan memetakan kode wilayah asalnya.
- Menyediakan antarmuka dashboard untuk pemantauan *real-time*, riwayat deteksi, dan statistik.

---

## 2. Stack Teknologi (Tech Stack)
Sistem ini dirancang untuk dapat dide-deploy pada lingkungan *shared hosting* (seperti cPanel) yang mendukung aplikasi Python, atau di VPS standar.

### Backend (API & ML Engine)
*   **Framework:** FastAPI (Python) - Dipilih karena sangat cepat, mendukung proses asinkron (async), dan cocok untuk melayani model Machine Learning serta WebSocket.
*   **Database:** MySQL - Relational database untuk menyimpan riwayat deteksi, konfigurasi kamera, dan *lookup* data kendaraan.
*   **ORM:** SQLAlchemy - Mengelola interaksi dengan database MySQL.
*   **Komunikasi Real-time:** WebSocket (Native FastAPI) - Digunakan untuk memancarkan *live video feed* dan hasil deteksi langsung ke frontend tanpa *polling*.

### Machine Learning & Computer Vision
*   **Object Detection:** YOLOv8 (Ultralytics) - Digunakan untuk mendeteksi area/bounding box plat nomor pada suatu gambar/frame.
*   **OCR Engine:** PaddleOCR - Library OCR berperforma tinggi untuk mengekstrak karakter huruf dan angka dari potongan gambar plat nomor.
*   **Image Processing:** OpenCV (`opencv-python-headless`) & NumPy - Digunakan untuk memanipulasi gambar (cropping, resizing, grayscaling, denoising, sharpening).

### Frontend (Dashboard SPA)
*   **Framework:** Vue.js 3 + Vite - Membangun antarmuka Single Page Application (SPA) yang interaktif dan responsif.
*   **State Management:** Pinia - Mengelola *state* aplikasi seperti data deteksi, status kamera, dll.
*   **Routing:** Vue Router.
*   **Styling:** Tailwind CSS - Framework utility-first untuk mempercepat pembuatan desain antarmuka yang bersih dan modern.
*   **HTTP Client:** Axios.

---

## 3. Arsitektur Sistem

Arsitektur aplikasi terbagi menjadi Frontend (Klien) dan Backend (Server/AI Worker).

```text
[DASHBOARD (Vue.js)] 
       |
       | (HTTP REST API / WebSocket)
       v
[BACKEND API (FastAPI)] 
       |
       +---> [Modul Stream] -> Menangkap RTSP dari CCTV
       |
       +---> [Modul ML / Image Processing]
       |         |-- 1. YOLOv8 (Deteksi Bounding Box Plat)
       |         |-- 2. OpenCV (Pre-processing: Denoise, Grayscale)
       |         |-- 3. PaddleOCR (Membaca Teks Plat)
       |         |-- 4. Validator (Regex Format Plat Indonesia)
       |
       +---> [Database MySQL] -> Menyimpan Log Deteksi & Master Kendaraan
```

---

## 4. Alur Logika Sistem (Detail Logic)

Sistem menangani pemrosesan dari dua jalur utama: **Upload File** dan **Live Stream (CCTV)**.

### A. Logika Pemrosesan Upload (Gambar / Video)
1.  **Penerimaan File:** Pengguna mengunggah file melalui antarmuka web. Frontend mengirim POST request multipart ke endpoint `/api/detect`.
2.  **Deteksi Objek (YOLOv8):** Backend memproses gambar. Model YOLO mencari objek yang diklasifikasikan sebagai plat nomor dan menghasilkan koordinat kotak pembatas (*bounding box*).
3.  **Cropping & Preprocessing:** 
    *   Sistem memotong (*crop*) area gambar tepat di koordinat plat nomor.
    *   Potongan gambar lalu diproses dengan OpenCV: diperbesar (jika resolusi terlalu kecil), diubah menjadi hitam putih (*grayscale*), dihilangkan *noise*-nya (Denoise), dan dipertajam (*Sharpen*). Hal ini agar mesin OCR dapat membaca dengan tingkat akurasi tinggi.
4.  **Ekstraksi Teks (PaddleOCR):** Potongan gambar yang sudah di- *enhance* dimasukkan ke PaddleOCR untuk mengambil teks (alfanumerik) dan mengembalikan teks dengan skor kepercayaan (*confidence score*).
5.  **Pembersihan & Validasi (Regex):** 
    *   Menghapus spasi ganda atau karakter aneh dari teks OCR.
    *   Melewati teks melalui filter Regex khusus format plat Indonesia `[Kode Wilayah] [Angka] [Seri]`.
    *   Jika cocok, sistem juga memetakan wilayahnya (misalnya: 'B' -> 'DKI Jakarta', 'D' -> 'Bandung').
    *   Pengecekan plat khusus seperti TNI, POLRI, atau CD juga ditangani oleh modul Regex.
6.  **Penyimpanan:** Hasil ekstraksi (Gambar asli dengan kotak, potongan gambar plat, teks plat, tingkat akurasi, asal wilayah) disimpan ke database MySQL.
7.  **Response:** Backend mengembalikan JSON *response* yang berisi detail plat ke frontend untuk ditampilkan.

### B. Logika Pemrosesan Live Stream (WebSocket)
1.  **Koneksi:** Frontend membuka jalur WebSocket ke `/ws/stream/{camera_id}`.
2.  **RTSP Capture:** Backend membuka koneksi *stream* ke IP Camera (menggunakan protokol RTSP melalui OpenCV).
3.  **Frame Sampling:** Alih-alih memproses setiap *frame* video (yang akan membebani CPU/GPU), sistem dikonfigurasi untuk memproses 1 *frame* dari setiap N *frame* (misalnya memproses deteksi setiap 5 *frame*).
4.  **Eksekusi ML Pipeline:** Pada *frame* yang terpilih, alur deteksi YOLO -> Crop -> Preprocess -> PaddleOCR -> Validasi dijalankan (sama seperti proses upload).
5.  **Broadcasting:** Backend mengubah *frame* saat itu menjadi format `base64` gambar JPEG, kemudian mengirimkannya bersama payload JSON yang berisi kotak deteksi dan teks plat kembali ke antarmuka web melalui WebSocket.
6.  **Real-Time Rendering:** Frontend menerima *frame* dan menampilkannya, sambil melakukan *overlay* kotak deteksi dan riwayat data di tabel secara instan.

---

## 5. Model Machine Learning

Sistem ini bergantung pada dua model kecerdasan buatan utama yang bekerja secara berurutan:

### 1. YOLOv8 (You Only Look Once - version 8)
*   **Versi Model:** Menggunakan varian `yolov8n.pt` (Nano). Model ini dipilih karena sangat ringan dan mampu berjalan cukup cepat di lingkungan dengan spesifikasi CPU terbatas (seperti *shared hosting* atau VPS murah).
*   **Fungsi:** Menentukan lokasi persis plat nomor di dalam sebuah gambar (mendapatkan titik X dan Y *bounding box*).
*   **Training/Fine-Tuning:** Meskipun model pre-trained COCO dari YOLOv8 bisa mendeteksi kendaraan, agar sistem lebih robust, model ini disarankan di-*fine-tune* khusus menggunakan dataset "Indonesian License Plates" (dapat bersumber dari Roboflow) sehingga YOLO langsung dapat mengklasifikasikan kelas `license_plate`.

### 2. PaddleOCR
*   **Fungsi:** Mengubah piksel gambar plat menjadi representasi *string* / teks.
*   **Konfigurasi:** Diatur menggunakan parameter `use_angle_cls=True` (untuk menangani kemiringan plat pada gambar yang tidak sempurna/sejajar) dan bahasa `lang='en'` (karena plat Indonesia menggunakan standar karakter Latin/Inggris dasar).
*   **Kelebihan:** PaddleOCR menangani variasi pencahayaan dan kontras sangat baik, terutama jika didahului dengan pre-processing gambar.

---

## 6. Detail Validasi Plat Nomor & Wilayah

*Logic* inti pada `plate_validator.py` menjamin bahwa data sampah hasil deteksi bisa dihindari.
Sistem menggunakan Regular Expression (Regex) seperti berikut:
`^([A-Z]{1,2})\s?(\d{1,4})\s?([A-Z]{1,3})$`

**Proses pemetaan wilayah:**
Jika OCR mendeteksi: **"B 1234 ABC"**
1. Sistem membaca Prefix `B`.
2. Mencocokkan dengan *Dictionary Map* kode wilayah (misal: `{"B": "DKI Jakarta", "L": "Surabaya", "D": "Bandung"}`).
3. Sistem secara otomatis memberikan *tag* wilayah "DKI Jakarta" pada laporan deteksi tersebut.

Ada juga pola khusus yang dievaluasi sebelum pola reguler:
`^(TNI|POLRI|CD|RF|RFH|RFS|RFP|RFD|RFL)\s?\d+`
Ini berguna untuk mendeteksi kendaraan aparat, militer, dan korps diplomatik.

---

## 7. Penutup
ALPR Indonesia ini dibangun dengan memadukan kemampuan AI generasi baru dengan optimasi *engineering* backend. Pemilihan FastAPI sangat vital dalam menjaga agar proses model *machine learning* dan *stream video* tidak memblokir antarmuka, sementara Vue.js memberikan pengalaman pengguna layaknya aplikasi *native* pada browser.
