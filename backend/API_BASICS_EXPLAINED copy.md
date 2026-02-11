# 📚 Penjelasan Konsep API untuk Pemula

**Panduan mudah dipahami untuk konsep-konsep backend ERGODRIVE**

---

## 🎯 Apa itu API?

**API = Application Programming Interface**

### Analogi Sederhana: Restoran

Bayangkan Anda di **restoran**:

| Komponen | Di Restoran | Di API |
|----------|-------------|--------|
| **Anda** | Pelanggan | Browser/Frontend |
| **Menu** | Daftar makanan | API Endpoints (URL) |
| **Pelayan** | Yang terima order | API Server (FastAPI) |
| **Dapur** | Tempat masak | Database |
| **Order** | "Saya mau nasi goreng" | HTTP Request |
| **Makanan** | Nasi goreng jadi | HTTP Response (data) |

**Cara kerja:**
1. Anda (client) baca menu (API docs)
2. Panggil pelayan (HTTP request ke endpoint)
3. Pelayan kasih order ke dapur (query database)
4. Dapur masak (proses data)
5. Pelayan bawa makanan (response)

---

## 🔐 1. JWT Authentication

**JWT = JSON Web Token**

### Analogi: Kartu Member Restoran

Bayangkan restoran punya **program membership**:

```
TANPA JWT (Tanpa Kartu Member):
├── Anda: "Saya mau pesan"
├── Pelayan: "Siapa Anda? Tunjukkan KTP dulu!"
└── Anda harus tunjukkan KTP SETIAP KALI pesan
    (Ribet & tidak aman)

DENGAN JWT (Pakai Kartu Member):
├── Anda: Login sekali → dapat kartu member
├── Kartu berisi: Nama, ID, tanggal expired
├── Setiap pesan, tunjukkan kartu aja
└── Pelayan langsung tahu Anda siapa tanpa cek KTP lagi
    (Cepat & aman)
```

### Di ERGODRIVE:

```javascript
// 1. Login (dapat JWT token)
POST /api/v1/auth/login
Body: { email: "user@test.com", password: "pass123" }

Response: {
  access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  refresh_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ8...",
  token_type: "bearer"
}

// 2. Pakai token untuk request selanjutnya
GET /api/v1/sessions
Headers: {
  Authorization: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

// Server baca token → tahu Anda siapa tanpa login lagi!
```

**Manfaat JWT:**
- ✅ Login sekali, pakai berkali-kali
- ✅ Aman (encrypted)
- ✅ Ada expired date (keamanan)
- ✅ Server tidak perlu simpan session di memory

---

## 📋 2. Sessions (Driving Sessions)

**Bukan "login session", tapi "driving session" (sesi berkendara)**

### Analogi: Booking Lapangan Futsal

```
BOOKING LAPANGAN FUTSAL:
├── Nama Booking: "Main bareng teman"
├── Mulai: 15 Januari 2026, 19:00
├── Selesai: 15 Januari 2026, 21:00
├── Durasi: 2 jam
├── Field: Lapangan A
└── Peserta: 10 orang
```

### Di ERGODRIVE (Driving Session):

```javascript
CREATE SESSION:
POST /api/v1/sessions
{
  "session_name": "Test Drive Malam",
  "device_type": "Muse 2",
  "settings": {
    "difficulty": "medium",
    "weather": "rain"
  }
}

Response: {
  "id": "abc-123-def",
  "session_name": "Test Drive Malam",
  "started_at": "2026-01-15T19:00:00Z",
  "session_status": "active",
  ...
}
```

**Apa yang tersimpan di session:**
- 🚗 Data mengemudi (kecepatan, lane deviation)
- 🧠 Data EEG (brainwave measurements)
- 😴 Alert fatigue (kapan driver ngantuk)
- 👁️ Face detection (mata merem, menguap)

**Manfaat:**
- ✅ Semua data satu sesi tersimpan berkelompok
- ✅ Bisa review ulang nanti: "Kapan saya paling ngantuk?"
- ✅ Bandingkan sessions: "Sesi pagi vs sesi malam"

---

## 🔌 3. WebSocket

**WebSocket = Komunikasi Real-time 2 arah**

### Analogi: Telepon vs SMS

```
HTTP (Biasa):
├── Client: "Halo server, ada update?"
├── Server: "Tidak ada"
├── (10 detik kemudian)
├── Client: "Halo server, ada update?"
├── Server: "Tidak ada"
└── Terus-terusan tanya (polling = boros!)

WebSocket:
├── Client: "Halo server, hubungkan aku"
├── Server: "OK, channel terbuka"
├── (Channel tetap terbuka)
├── Server: "Ada update!" → langsung kirim
├── Client: "Terima!" → langsung terima
└── Komunikasi 2 arah real-time!
```

### Di ERGODRIVE:

**Kenapa perlu WebSocket?**

EEG device kirim data **256 samples per detik**!
- Kalau pakai HTTP biasa → kirim 256 request/detik (lambat!)
- Pakai WebSocket → 1 connection, streaming terus (cepat!)

```javascript
// 1. Buka WebSocket connection
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/session/abc-123');

// 2. Server kirim data real-time
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  // Contoh data EEG
  {
    type: "eeg_data",
    timestamp: "2026-01-15T19:00:01.234Z",
    theta_alpha_ratio: 0.85,  // Indikator ngantuk!
    fatigue_score: 75
  }
  
  // Langsung tampilkan di dashboard!
  updateFatigueGauge(data.fatigue_score);
};

// 3. Client juga bisa kirim data
ws.send(JSON.stringify({
  type: "face_detection",
  eyes_closed: true,
  yawning: false
}));
```

**Manfaat:**
- ✅ Real-time (tidak ada delay)
- ✅ Efisien (1 connection untuk banyak data)
- ✅ 2 arah (server & client bisa kirim kapan saja)

**Kapan pakai HTTP vs WebSocket:**
- HTTP: Login, create session, get list (sekali-kali)
- WebSocket: Streaming EEG, game events (terus-menerus)

---

## 📏 4. Pydantic Schemas

**Pydantic = Validator data otomatis**

### Analogi: Template Formulir

Bayangkan Anda isi **formulir pendaftaran SIM**:

```
TANPA PYDANTIC (Manual Check):
├── User isi: Email = "bukan-email"
├── Server: Terima aja dulu
├── Simpan ke database
├── ERROR! Format email salah
└── Data rusak! 😱

DENGAN PYDANTIC (Auto Validation):
├── User isi: Email = "bukan-email"
├── Pydantic: "ERROR! Email harus format: xxx@yyy.com"
├── Tolak sebelum masuk database
└── Data aman! ✅
```

### Di ERGODRIVE:

**Definisi Schema:**
```python
# app/schemas/auth.py
class RegisterRequest(BaseModel):
    email: EmailStr  # Harus format email valid
    password: str = Field(..., min_length=8)  # Min 8 karakter
    full_name: str = Field(..., min_length=2, max_length=255)
    role: str = Field(default="student", pattern="^(student|researcher|admin)$")
```

**Tanpa Pydantic:**
```python
# Terima data mentah, cek manual
def register(data):
    if '@' not in data['email']:  # Cek manual email
        return error
    if len(data['password']) < 8:  # Cek manual password
        return error
    if data['role'] not in ['student', 'researcher']:  # Cek manual role
        return error
    # ... banyak cek lainnya
```

**Dengan Pydantic:**
```python
# Otomatis validated!
def register(data: RegisterRequest):
    # Data sudah pasti valid!
    # Pydantic sudah cek semuanya
    create_user(data)
```

**Manfaat:**
- ✅ Auto validation (email, password, dll)
- ✅ Type checking (integer harus integer, bukan string)
- ✅ Default values (role default = "student")
- ✅ Error messages jelas
- ✅ Auto documentation (Swagger UI baca schema)

---

## 📦 5. Virtual Environment (venv)

**Virtual Environment = Folder terpisah untuk Python packages**

### Analogi: Lemari Baju Terpisah per Project

```
TANPA VIRTUAL ENVIRONMENT:
├── Laptop Anda (Global Python)
│   ├── Project A butuh: FastAPI v0.100
│   ├── Project B butuh: FastAPI v0.109
│   └── KONFLIK! Tidak bisa install 2 versi berbeda
│       (Salah satu project pasti error)

DENGAN VIRTUAL ENVIRONMENT:
├── Laptop Anda
│   ├── Project A
│   │   └── venv-A/ (FastAPI v0.100 di sini)
│   └── Project B
│       └── venv-B/ (FastAPI v0.109 di sini)
└── Tidak konflik! Masing-masing punya library sendiri
```

### Di ERGODRIVE:

**Struktur:**
```
C:\Users\User\Fumorive\backend\
├── venv/                    ← Virtual environment
│   ├── Scripts/
│   │   └── python.exe      ← Python khusus project ini
│   └── Lib/
│       └── site-packages/  ← FastAPI, SQLAlchemy, dll
├── main.py
└── requirements.txt         ← Daftar library yang dibutuhkan
```

**Kenapa perlu?**

1. **Isolasi project:**
   ```
   ERGODRIVE Project:
   ├── FastAPI 0.109
   ├── SQLAlchemy 2.0.25
   └── Pydantic 2.5.3
   
   Project Lain (di laptop yang sama):
   ├── FastAPI 0.95 (versi lama)
   ├── Django 4.2
   └── Tidak konflik dengan ERGODRIVE!
   ```

2. **Portability:**
   ```bash
   # Developer A
   pip freeze > requirements.txt
   # Share file requirements.txt
   
   # Developer B (laptop berbeda)
   pip install -r requirements.txt
   # Install exact same versions!
   ```

3. **Clean system:**
   ```
   Tanpa venv:
   ├── Install 1000+ packages globally
   └── Laptop jadi lambat & berantakan
   
   Dengan venv:
   ├── Packages hanya di folder project
   └── Delete folder → bersih!
   ```

**Cara pakai:**
```bash
# Activate (setiap kali development)
.\venv\Scripts\activate  # Windows

# Sekarang Python pakai yang di venv/
python --version  # Python dari venv/Scripts/python.exe
pip list          # Lihat packages di venv/, bukan global

# Deactivate (kalau selesai)
deactivate
```

---

## 🔗 Bagaimana Semuanya Bekerja Bersama di ERGODRIVE

```
┌─────────────────────────────────────────────────────┐
│  USER (Driver pakai EEG device)                     │
└─────────────────────────────────────────────────────┘
    │
    │ 1. Login (JWT)
    │
    ↓
┌─────────────────────────────────────────────────────┐
│  POST /api/v1/auth/login                            │
│  - Pydantic validate email & password               │
│  - Return JWT token                                 │
└─────────────────────────────────────────────────────┘
    │
    │ 2. Create Session
    │
    ↓
┌─────────────────────────────────────────────────────┐
│  POST /api/v1/sessions (dengan JWT token)          │
│  - Pydantic validate session data                   │
│  - Create session record di database               │
└─────────────────────────────────────────────────────┘
    │
    │ 3. Start Driving (WebSocket)
    │
    ↓
┌─────────────────────────────────────────────────────┐
│  WS /api/v1/ws/session/{id}                         │
│  - Real-time streaming EEG data                     │
│  - Pydantic validate setiap data point              │
│  - Save ke database (sessions table)                │
└─────────────────────────────────────────────────────┘
    │
    │ 4. Monitor Real-time
    │
    ↓
┌─────────────────────────────────────────────────────┐
│  Dashboard menampilkan:                             │
│  - Fatigue score (dari EEG)                         │
│  - Eye closure (dari face detection)                │
│  - Game events (lane deviation)                     │
│  - Alerts (warning ngantuk!)                        │
└─────────────────────────────────────────────────────┘
```

**Semua konsep dipakai bersamaan:**
- JWT → Authentikasi user
- Session → Kelompokkan data driving
- WebSocket → Stream data real-time
- Pydantic → Validate semua data
- Venv → Isolasi dependencies

---

## 📊 Ringkasan Singkat

| Konsep | Simple Explanation | Kenapa Penting? |
|--------|-------------------|-----------------|
| **JWT** | Kartu member digital | Login sekali, pakai berkali-kali |
| **Session** | Sesi berkendara | Kelompokkan semua data 1 trip |
| **WebSocket** | Telepon (bukan SMS) | Real-time streaming EEG data |
| **Pydantic** | Auto-validator | Pastikan data valid sebelum simpan |
| **Venv** | Lemari terpisah | Tidak konflik dengan project lain |

---

## 🎯 Latihan Pemahaman

**Scenario:** User mau mulai driving session dengan EEG monitoring

**Pertanyaan:** Konsep mana yang dipakai?

```
1. User buka app → Login
   → Konsep: JWT Authentication ✅
   
2. User klik "Start New Session"
   → Konsep: Session (create driving session) ✅
   
3. EEG device mulai kirim data 256x/detik
   → Konsep: WebSocket (real-time streaming) ✅
   
4. Setiap data harus valid sebelum simpan
   → Konsep: Pydantic (validation) ✅
   
5. Programmer lain clone project, install dependencies
   → Konsep: Virtual Environment ✅
```

**Semua konsep terpakai!** 🎉

---

## 📚 Resources untuk Belajar Lebih

- **JWT**: https://jwt.io/introduction
- **WebSocket**: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
- **Pydantic**: https://docs.pydantic.dev/latest/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Virtual Environment**: https://docs.python.org/3/tutorial/venv.html

---

**Last Updated**: 16 Januari 2026  
**Untuk pertanyaan lebih lanjut**: Tanya aja! 😊
