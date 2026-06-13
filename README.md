# Sara Nusantara – Smart AI Reservation Assistant

> **Capstone Project · CAMP Batch 4 · Kelompok 3 – Hana Jatmiana · 2026**

Platform manajemen reservasi restoran berbasis AI yang dibangun dengan **Streamlit** dan didukung oleh **Google Gemini 2.5 Flash**. Aplikasi ini menyediakan dua mode akses — portal pelanggan untuk reservasi via chatbot AI, dan portal admin dengan dashboard analitik bisnis lengkap.

---

## Struktur Project

```
cloned_repo/
├── Beranda.py                      # Entry point – chatbot Sara Nusantara & login admin
├── utils.py                        # Data loader, shared CSS, konstanta warna
├── data.json                       # Dataset sintetis 500 reservasi (local fallback)
├── requirements.txt                # Dependensi Python
├── README.md
├── .env                            # API key (tidak di-commit ke Git)
├── .gitignore
├── assets/                         # Logo dan aset gambar
├── styles/
│   ├── main.css                    # CSS halaman chat (Beranda)
│   └── admin.css                   # CSS kelas status badge (future use)
├── .streamlit/
│   └── config.toml                 # Tema warna & konfigurasi server
└── pages/
    ├── 1_Dashboard_Analytics.py    # Dashboard KPI & visualisasi Plotly
    └── 2_Reservation_Management.py # Manajemen & detail reservasi
```

---

## Cara Menjalankan

### 1. Clone / Download Project

```bash
git clone https://github.com/dnldsmrr/Smart-Reservation-Restaurantt.git
cd Smart-Reservation-Restaurantt
```

### 2. Buat Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi API Key

Buat file `.env` di folder root project:

```env
GOOGLE_API_KEY="isi_dengan_api_key_gemini_kamu"
```

> Dapatkan API key gratis di [Google AI Studio](https://aistudio.google.com/app/apikey).

### 5. Jalankan Aplikasi

```bash
streamlit run Beranda.py
```

Akses di browser: **http://localhost:8501**

---

## Sistem Login Admin

Login admin menggunakan tombol **Masuk** di pojok kanan atas header. Klik tombol → masukkan password → klik Verifikasi.

**Password default:** `admin123`

Setelah login, admin diarahkan ke Dashboard Analytics dan dapat mengakses semua halaman admin via sidebar.

> Untuk production, simpan password sebagai environment variable.

---

## Fitur

### Halaman Chat – Sara Nusantara

Chatbot AI yang ditenagai **Google Gemini 2.5 Flash** untuk membantu pelanggan:

- **Buat Reservasi** – mengumpulkan nama, jumlah tamu, tanggal, waktu, area, dan occasion
- **Cek Status Reservasi** – mencari berdasarkan nama atau Reservation ID
- **Info Restoran** – jam buka, menu, fasilitas, lokasi
- **Fallback heuristik** – tetap bisa merespons meski API tidak tersedia

Pipeline AI: `detect_intent()` → `extract_params()` → `heuristic_response()` → (fallback) `call_gemini()`

### Dashboard Analytics

Hanya dapat diakses admin. Filter global: Bulan, Status Reservasi, Area Meja.

| Kategori | Visualisasi |
|---|---|
| Overview KPI | Total Reservasi, Revenue, Rating, Pelanggan Unik, breakdown status |
| Reservation Analytics | Tren bulanan, distribusi status, channel booking, area meja, occasion |
| Revenue Analytics | Revenue per channel, per area, per occasion, tren bulanan |
| Customer Analytics | Party size, distribusi rating, metode pembayaran |

### Manajemen Reservasi

Hanya dapat diakses admin.

- Cari berdasarkan nama, Reservation ID, atau Customer ID
- Filter Status, Area Meja, Channel Booking, rentang tanggal
- Tabel paginasi dengan klik-ke-detail
- Panel detail lengkap: kontak, tanggal, area, tamu, occasion, status, pembayaran, rating, catatan
- Export hasil filter ke CSV

---

## Arsitektur Data

`load_data()` di `utils.py` mencoba koneksi Railway MySQL terlebih dahulu. Jika MySQL kosong atau tidak tersedia, fallback ke `data.json`. Reservasi baru dari chatbot ditulis ke `data.json` lalu disinkronkan ke MySQL.

### Koneksi MySQL (Railway)

```
Host    : thomas.proxy.rlwy.net
Port    : 21018
DB      : railway
Table   : reservations
```

Kredensial dapat di-override via environment variable (`MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`).

---

## Desain & UI

### Color Tokens (`utils.py`)

| Token | Hex | Penggunaan |
|---|---|---|
| `GOLD` | `#FF6B35` | Terracotta – primary accent, button, border |
| `DARK` | `#2D2522` | Charcoal – heading, teks utama |
| `CREAM` | `#FFFBF8` | Warm off-white – background halaman |

### Tipografi

- **Outfit** – heading, judul section, nilai KPI
- **Inter** – body text, label, badge

### Icons

Material Symbols (Google Fonts CDN) digunakan di seluruh halaman via:
- `":material/icon_name:"` untuk widget Streamlit
- `<span class="material-symbols-outlined">icon_name</span>` untuk HTML

### Komponen CSS Reusable

Didefinisikan di `COMMON_CSS` (`utils.py`), digunakan di kedua halaman admin:

| Class | Deskripsi |
|---|---|
| `.kpi-card` | Card KPI dengan border kiri aksen |
| `.section-title` | Judul section dengan garis gradient |
| `.badge` | Pill label inline |
| `.back-button` | Tombol gradient terracotta |

---

## Teknologi

| Layer | Stack |
|---|---|
| Framework | Streamlit 1.58+ |
| Visualisasi | Plotly Express & Graph Objects |
| Data Processing | Pandas, JSON |
| AI / LLM | Google Gemini 2.5 Flash (via REST API) |
| Database | Railway MySQL + local JSON fallback |
| Environment | python-dotenv |
| Icons | Google Material Symbols (CDN) |

---

## Tim Pengembang

| Anggota | Peran |
|---|---|
| Achmad Raka Yuniar | Project Leader & Backend Developer |
| William Yonathan | AI Engineer |
| Milda Khaerunnisa | Data & Analytics Developer |
| Muhammad Ad'hiya Hartono | Frontend & UI/UX Developer |
| Alfin Agustiar Pratama | QA & Integration Engineer |
| Arya | Data Scientist & Deployment |

> Dibimbing oleh **Hana Jatmiana** – Mentor Kelompok 3, CAMP Batch 4

---

## Lisensi

Project ini dibuat sebagai capstone project untuk keperluan akademis dalam program **Data Science & Generative AI – CAMP Batch 4**. Tidak untuk distribusi komersial.

---

*© 2026 Sara Nusantara · Smart AI Reservation Assistant · Kelompok 3 Hana Jatmiana*
