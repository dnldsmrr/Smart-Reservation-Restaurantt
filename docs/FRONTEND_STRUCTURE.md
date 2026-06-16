# Struktur Frontend – Sara Nusantara
### Dokumentasi Presentasi · Kelompok 3 CAMP Batch 4

---

## Daftar Isi

1. [Peta File Frontend](#1-peta-file-frontend)
2. [Sistem Tipografi & Font](#2-sistem-tipografi--font)
3. [Sistem Warna](#3-sistem-warna)
4. [Arsitektur CSS – Tiga Lapisan](#4-arsitektur-css--tiga-lapisan)
5. [Komponen Reusable](#5-komponen-reusable)
6. [Struktur Tiap Halaman](#6-struktur-tiap-halaman)
7. [Nav Bar – Desain & Implementasi](#7-nav-bar--desain--implementasi)
8. [Sidebar & FAB System](#8-sidebar--fab-system)
9. [Chat Interface (Beranda)](#9-chat-interface-beranda)
10. [Alur Render Streamlit](#10-alur-render-streamlit)

---

## 1. Peta File Frontend

```
Sara Nusantara/
│
├── Beranda.py                      ← Halaman chat publik (entry point)
├── utils.py                        ← Shared CSS, warna, helper
│
├── pages/
│   ├── 1_Dashboard_Analytics.py   ← Admin: KPI + chart Plotly
│   └── 2_Reservation_Management.py← Admin: tabel reservasi + detail
│
├── styles/
│   ├── main.css                   ← CSS halaman chat Beranda
│   └── admin.css                  ← CSS badge status (cadangan / future)
│
├── assets/
│   └── sara_logo.png              ← Logo dipakai di nav bar semua halaman
│
└── .streamlit/
    └── config.toml                ← Tema warna & konfigurasi Streamlit
```

### Tanggung Jawab Tiap File

| File | Peran Frontend |
|---|---|
| `Beranda.py` | Halaman chat, nav bar + popover login, chat balloon, quick-action buttons |
| `pages/1_Dashboard_Analytics.py` | Nav bar admin, KPI cards, chart Plotly, sidebar filter |
| `pages/2_Reservation_Management.py` | Nav bar admin, tabel paginasi, panel detail, export CSV |
| `utils.py` | `COMMON_CSS` (shared admin), konstanta warna `GOLD / DARK / CREAM` |
| `styles/main.css` | Semua styling halaman chat (balloon, input, layout, sidebar) |
| `styles/admin.css` | Badge status reservasi, card area meja (siap pakai bila dibutuhkan) |
| `.streamlit/config.toml` | Tema warna dasar Streamlit, font, background |

---

## 2. Sistem Tipografi & Font

### Font yang Digunakan

| Font | Sumber | Dipakai untuk |
|---|---|---|
| **Outfit** | Google Fonts | Heading, judul section, nilai KPI, nama brand di nav bar |
| **Inter** | Google Fonts | Body text, label form, badge, teks paragraf, chip |
| **Material Symbols Outlined** | Google Fonts | Semua ikon di tombol, nav, dan konten HTML |

### Cara Font Dimuat

Font dimuat via CDN Google Fonts di dua tempat:

**1. Di `styles/main.css`** (untuk halaman Beranda):
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800
             &family=Outfit:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:
             opsz,wght,FILL,GRAD@20,500,0,0');
```

**2. Di `COMMON_CSS` dalam `utils.py`** (untuk halaman admin):
```css
/* Baris pertama di COMMON_CSS – selalu di-load duluan */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800
             &family=Outfit:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:
             opsz,wght,FILL,GRAD@20,500,0,0');
```

### Hierarki Penggunaan Font

```
Outfit Bold (700–800)
  ├── Nama brand "Sara Nusantara" di nav bar
  ├── Judul section (.section-title)
  └── Nilai angka besar di KPI card (.kpi-value, font-size: 2rem)

Inter Regular–Bold (400–700)
  ├── Body text, paragraf chat
  ├── Label form, caption, badge
  ├── Chip nav bar (.sara-nav-chip)
  └── Teks tabel & detail reservasi
```

### Skala Ukuran Teks

| Elemen | Font | Size | Weight |
|---|---|---|---|
| Nama brand nav bar | Outfit | 18px | 800 |
| Nilai KPI | Outfit | 2rem ≈ 32px | 700 |
| Judul section | Outfit | 1.35rem ≈ 22px | 700 |
| Body / paragraf chat | Inter | 15px | 400 |
| Label badge / chip | Inter | 12px | 600 |
| Caption sub-KPI | Inter | 0.8rem ≈ 13px | 400 |
| Label KPI (uppercase) | Inter | 0.78rem ≈ 12px | 600 |

---

## 3. Sistem Warna

### Color Tokens (didefinisikan di `utils.py`)

```python
GOLD  = "#FF6B35"   # Terracotta — aksen utama, tombol, border, ikon
DARK  = "#2D2522"   # Charcoal   — heading, teks utama
CREAM = "#FFFBF8"   # Warm white — background chip, surface terang
```

### Palet Lengkap

| Token / Nama | Hex | Digunakan di |
|---|---|---|
| `GOLD` / Terracotta | `#FF6B35` | Tombol, border kiri KPI, section underline, chat balloon user, ikon aktif |
| `GOLD` gradient end | `#FF8E66` | Gradient tombol, FAB, back-button |
| `DARK` / Charcoal | `#2D2522` | Heading, teks body chat balloon kiri, nilai KPI |
| `CREAM` | `#FFFBF8` | Background nav chip, surface terang |
| White | `#FFFFFF` | Nav bar, sidebar, balloon kiri (asisten), KPI card |
| Light gray bg | `#F4F4F4` | Background area konten utama |
| Border gray | `#EAEAEA` / `#E5E5E5` | Border nav bar, sidebar, balloon asisten |
| Subtitle gray | `#8E8E8E` | Subtitle nav bar, keterangan kecil |
| KPI label gray | `#888888` | Label uppercase di KPI card |
| Sub-text gray | `#AAAAAA` | Teks keterangan kecil di bawah KPI |

### Tema di `config.toml`

```toml
[theme]
primaryColor            = "#FF6B35"   # Warna tombol default Streamlit
backgroundColor         = "#FFFBF8"   # Background halaman
secondaryBackgroundColor = "#FFFFFF"  # Background sidebar / input
textColor               = "#2D2522"   # Warna teks default
```

### Status Colors (untuk badge reservasi)

```python
# Di utils.py
STATUS_COLORS = {
    "confirmed": "#28A745",   # Hijau
    "completed": "#007BFF",   # Biru
    "pending":   "#FFA500",   # Oranye
    "cancelled": "#DC3545",   # Merah
    "no_show":   "#6C757D",   # Abu-abu
}
```

---

## 4. Arsitektur CSS – Tiga Lapisan

```
┌─────────────────────────────────────────────────┐
│  LAPISAN 3 – Inline per halaman                 │
│  st.markdown("<style>...</style>")              │
│  → Fine-tuning spesifik, nav bar CSS, FAB       │
├─────────────────────────────────────────────────┤
│  LAPISAN 2 – Shared admin (COMMON_CSS)          │
│  utils.py → st.markdown(COMMON_CSS, ...)        │
│  → Font, sidebar, tombol, KPI, section-title    │
├─────────────────────────────────────────────────┤
│  LAPISAN 1 – File eksternal / tema              │
│  styles/main.css + .streamlit/config.toml       │
│  → Tema dasar, chat layout, balloon styling     │
└─────────────────────────────────────────────────┘
         ↓ prioritas semakin tinggi ke atas
```

### Siapa Yang Pakai Apa

| Lapisan | File Sumber | Halaman Pemakai |
|---|---|---|
| `styles/main.css` | File CSS eksternal | `Beranda.py` saja (via `load_css()`) |
| `COMMON_CSS` di `utils.py` | String Python | `1_Dashboard_Analytics.py`, `2_Reservation_Management.py` |
| Inline `st.markdown("<style>")` | Per-halaman | Semua halaman (fine-tuning) |
| `config.toml` `[theme]` | Konfigurasi Streamlit | Global (semua halaman) |

### Kenapa Ada Tiga Lapisan?

- **`config.toml`** → mudah diubah, tapi terbatas (hanya 4 properti warna)
- **`main.css`** → khusus chat, pisah dari admin agar tidak saling tabrakan
- **`COMMON_CSS`** → admin pages punya kebutuhan yang sama (font, tombol, KPI card), DRY principle
- **Inline per halaman** → CSS kritis (nav bar `position:fixed`) harus di-inject saat rerun berlangsung, tidak bisa bergantung pada module yang bisa ter-cache

---

## 5. Komponen Reusable

Semua komponen berikut didefinisikan di `COMMON_CSS` (`utils.py`) dan tersedia di kedua halaman admin.

### `.kpi-card`

Card putih dengan border kiri berwarna. Warna border dikontrol via CSS variable `--accent`.

```html
<div class="kpi-card" style="--accent: #FF6B35;">
    <div class="kpi-label">TOTAL RESERVASI</div>
    <div class="kpi-value">508</div>
    <div class="kpi-sub">+12% vs bulan lalu</div>
</div>
```

**Properti utama:**
- Background: `white`, border-radius: `14px`
- Border kiri: `4px solid var(--accent, #FF6B35)`
- Shadow: `0 2px 12px rgba(0,0,0,0.05)`

---

### `.section-title`

Judul section dengan garis gradient oranye → transparan di sebelah kanan.

```html
<div class="section-title">
    <span class="material-symbols-outlined">bar_chart</span>
    Reservation Analytics
</div>
```

**Properti utama:**
- Font: `Outfit 700`, ukuran `1.35rem`, warna `#2D2522`
- Garis kanan: `::after` pseudo-element dengan `background: linear-gradient(to right, #FF6B35, transparent)`

---

### `.badge`

Pill label inline untuk status atau kategori.

```html
<span class="badge" style="background:#d4edda; color:#155724;">Confirmed</span>
<span class="badge" style="background:#fff3cd; color:#856404;">Pending</span>
```

**Properti utama:**
- `border-radius: 50px`, `padding: 3px 12px`, `font-size: 0.78rem`, `font-weight: 600`

---

### `.back-button`

Tombol CTA gradient terracotta dengan efek hover naik.

```html
<div class="back-button-wrapper">
    <a href="#" class="back-button">
        <span class="back-button-icon">←</span>
        Kembali ke Dashboard
    </a>
</div>
```

**Properti utama:**
- Gradient: `linear-gradient(135deg, #FF6B35, #FF8E66)`
- Shadow: `0 14px 32px rgba(255,107,53,0.18)`
- Hover: `translateY(-2px)`, shadow lebih tebal

---

### `.sara-nav-bar` & `.sara-nav-chip`

Nav bar fixed full-width dan chip badge di dalamnya.

```html
<div class="sara-nav-bar">
    <div><!-- kiri: logo + nama brand --></div>
    <div>
        <span class="sara-nav-chip">Admin Panel</span>
    </div>
</div>
```

**`.sara-nav-bar`:**
- `position: fixed`, `top:0`, `left:0`, `right:0`, `height: 72px`
- `z-index: 999998` (di bawah Streamlit header, di atas konten)
- Background: `white`, border bawah: `1px solid #EAEAEA`

**`.sara-nav-chip`:**
- Background: `#FFFBF8`, border: `1px solid #FFE0D3`
- Warna teks: `#FF6B35`, font: Inter 12px 600

---

## 6. Struktur Tiap Halaman

### Beranda.py – Halaman Chat

```
┌──────────────────────────────────────────────────────┐
│  Nav Bar (position:fixed, z-index:999998)            │
│  [Logo] Sara Nusantara · Online     [chip] [Masuk ▾] │
└──────────────────────────────────────────────────────┘
│
│  ← Sidebar (Beranda info restoran, jam buka)
│
┌──────────────────────────────────────────────────────┐
│  Greeting header (hanya tampil saat chat kosong)     │
│  "Selamat datang di Sara Nusantara"                  │
│                                                      │
│  Quick action buttons (4 kolom):                    │
│  [Buat Reservasi] [Cek Status] [Info] [Menu]        │
│                                                      │
│  ┄┄ Riwayat Chat ┄┄                                 │
│                         [Teks user]  ← oranye kanan │
│  [Teks asisten] →                    ← putih kiri   │
│                                                      │
└──────────────────────────────────────────────────────┘
│  [Chat input field]  [→ Kirim]                       │
└──────────────────────────────────────────────────────┘
│  Footer disclaimer (position:fixed, bawah)           │
```

**CSS sumber:** `styles/main.css` + inline di `Beranda.py`

---

### 1_Dashboard_Analytics.py – Dashboard Admin

```
┌──────────────────────────────────────────────────────┐
│  Nav Bar (position:fixed)                            │
│  [Logo] Sara Nusantara · Admin Panel     [chip]      │
└──────────────────────────────────────────────────────┘
│                                                      │
│  Sidebar ←  [☰] FAB bila sidebar tertutup           │
│  ─ Dashboard Analytics ←aktif                       │
│  ─ Kelola Reservasi                                  │
│  ─ Keluar Admin                                      │
│  ── Filter ──                                        │
│  Bulan / Status / Area                               │
│                                                      │
┌──────────────────────────────────────────────────────┐
│  Header card                                         │
│  "Dashboard Analytics" + subtitle                    │
│                                                      │
│  KPI Row 1: [Total Reservasi] [Revenue] [Rating]    │
│  KPI Row 2: [Pelanggan Unik] [Status breakdown]     │
│                                                      │
│  ── Reservation Analytics ──                        │
│  [Tren Bulanan] [Distribusi Status]                  │
│  [Channel Booking] [Area Meja] [Occasion]            │
│                                                      │
│  ── Revenue Analytics ──                            │
│  [Per Channel] [Per Area] [Tren Revenue]             │
│                                                      │
│  ── Customer Analytics ──                           │
│  [Party Size] [Rating Distribution] [Payment]        │
└──────────────────────────────────────────────────────┘
```

**CSS sumber:** `COMMON_CSS` + inline per halaman

---

### 2_Reservation_Management.py – Manajemen Reservasi

```
┌──────────────────────────────────────────────────────┐
│  Nav Bar (sama dengan Dashboard)                     │
└──────────────────────────────────────────────────────┘
│                                                      │
│  Sidebar ←                                          │
│  ─ Dashboard Analytics                              │
│  ─ Kelola Reservasi ←aktif                          │
│  ─ Keluar Admin                                      │
│                                                      │
┌──────────────────────────────────────────────────────┐
│  Search bar + filter (Status, Area, Channel, Tanggal)│
│                                                      │
│  Tabel Reservasi (paginasi 10 baris)                 │
│  [ID] [Nama] [Tanggal] [Tamu] [Area] [Status] [Klik]│
│  ← klik baris → buka panel detail                   │
│                                                      │
│  Panel Detail Reservasi                              │
│  Kontak · Tanggal & Waktu · Area & Meja             │
│  Occasion · Status · Pembayaran · Rating · Catatan  │
│                                                      │
│  [Export CSV]                                        │
└──────────────────────────────────────────────────────┘
```

**CSS sumber:** `COMMON_CSS` + inline per halaman

---

## 7. Nav Bar – Desain & Implementasi

Nav bar adalah elemen terpenting dari konsistensi visual. Muncul di **ketiga halaman** dengan konten sedikit berbeda.

### Kenapa HTML Murni, Bukan Widget Streamlit?

Streamlit merender widget dalam DOM-nya sendiri. Elemen `position: fixed` yang berisi widget Streamlit tidak bisa menerima klik secara konsisten karena Streamlit menggunakan `iframe` dan z-index stack yang kompleks. Solusinya:

- **Nav bar** → pure HTML via `st.markdown(..., unsafe_allow_html=True)` → statis, tidak ada klik
- **Tombol "Masuk"** → widget `st.popover()` Streamlit terpisah → diposisikan fixed via CSS khusus

### Perbandingan Nav Bar Antar Halaman

| Elemen | Beranda | Dashboard | Reservasi |
|---|---|---|---|
| Logo | `assets/sara_logo.png` (base64) | Sama | Sama |
| Nama brand | Sara Nusantara | Sara Nusantara | Sara Nusantara |
| Subtitle | `● Online · AI Reservation Assistant` | `● Admin Panel · Mandala Rasa` | `● Admin Panel · Mandala Rasa` |
| Chip kanan | `Sara Nusantara` | `Admin Panel` | `Admin Panel` |
| Elemen kanan tambahan | `st.popover("Masuk")` | — | — |

### Logo: Base64 Embedding

Logo tidak di-load sebagai URL biasa karena `position: fixed` HTML tidak selalu mengikuti base path Streamlit. Solusinya: encode PNG ke Base64 dan embed langsung di tag `<img>`:

```python
import base64, os

def _get_b64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

_logo_b64 = _get_b64(os.path.join(os.path.dirname(__file__), "assets", "sara_logo.png"))
_LOGO = f'<img src="data:image/png;base64,{_logo_b64}" style="width:44px;height:44px;border-radius:10px;">'
```

---

## 8. Sidebar & FAB System

### Mekanisme Collapse / Expand

Streamlit di layar lebar (≥1280px) selalu **memaksa sidebar terbuka** setiap rerun jika `initial_sidebar_state="auto"`. Solusi yang dipakai:

```python
# HARUS dijalankan SEBELUM st.set_page_config()
if "admin_sidebar_open" not in st.session_state:
    st.session_state.admin_sidebar_open = True

_sidebar_state = "expanded" if st.session_state.admin_sidebar_open else "collapsed"

st.set_page_config(
    ...
    initial_sidebar_state=_sidebar_state   # "expanded" atau "collapsed"
)
```

Session state membaca nilai yang ditetapkan sebelum re-render sehingga Streamlit menghormati state yang disimpan.

### FAB (Floating Action Button)

Ketika sidebar ditutup, tombol FAB oranye muncul di pojok kiri atas untuk membukanya kembali.

```
┌────────┐
│ [☰]   │  ← FAB oranye, muncul hanya saat sidebar collapsed
│        │     position: fixed, top:14px, left:14px
│        │     z-index: 9999990 (harus > stHeader 999990)
```

Teknik positioning FAB menggunakan CSS `:has()` selector untuk menargetkan tombol Streamlit berdasarkan marker HTML di sebelahnya:

```css
div.element-container:has(#sara-show-menu-marker) + div.element-container .stButton > button {
    position: fixed !important;
    top: 14px !important;
    left: 14px !important;
    z-index: 9999990 !important;
    width: 46px !important;
    height: 46px !important;
    border-radius: 12px !important;
    background: linear-gradient(135deg, #FF6B35, #FF8E66) !important;
}
```

**Kenapa z-index harus 9999990?** Streamlit `stHeader` punya z-index `999990` dan `pointer-events: auto`, sehingga klik pada elemen di bawahnya tidak akan terdaftar. FAB harus berada **di atas** header Streamlit.

---

## 9. Chat Interface (Beranda)

### Chat Balloon

Balon chat dibuat dengan menimpa gaya bawaan Streamlit menggunakan CSS `:has()`:

```
User (kanan)                          Asisten (kiri)
┌──────────────────────┐   ┌──────────────────────────┐
│ Background: #FF6B35  │   │ Background: white         │
│ Border-radius:        │   │ Border: 1px solid #EAEAEA │
│   18px 4px 18px 18px │   │ Border-radius:            │
│ Text: white          │   │   4px 18px 18px 18px      │
│ Shadow: oranye 20%   │   │ Text: #2D2522             │
└──────────────────────┘   └──────────────────────────┘
```

Avatar disembunyikan (`display: none`), alignment diatur via `justify-content: flex-end / flex-start`.

### Quick Action Buttons

Empat tombol yang muncul saat chat kosong. Menggunakan `st.button()` biasa dalam 4 kolom, dengan CSS override untuk tampilan "pill outline":

```css
button[kind="secondary"] {
    border-radius: 16px !important;
    border: 1px solid #E5E5E5 !important;
    background-color: #FFFFFF !important;
    color: #0D0D0D !important;
}
button[kind="secondary"]:hover {
    border-color: #FF6B35 !important;
    color: #FF6B35 !important;
}
```

### Popover Login

Tombol "Masuk" di pojok kanan nav bar menggunakan `st.popover()`:

```python
with st.popover("Masuk", use_container_width=False):
    st.markdown("**Login Admin**")
    pwd = st.text_input("Password", type="password")
    if st.button("Verifikasi"):
        if pwd == "admin123":
            st.session_state.admin_logged_in = True
            st.switch_page("pages/1_Dashboard_Analytics.py")
```

Posisi fixed-nya diatur via CSS:
```css
div[data-testid="stPopover"] {
    position: fixed !important;
    top: 14px !important;
    right: 2rem !important;
    z-index: 9999999 !important;
}
```

---

## 10. Alur Render Streamlit

Memahami urutan ini penting agar tidak salah meletakkan kode:

```
Script Python dijalankan dari atas ke bawah
        │
        ▼
1. Baca session_state (admin_logged_in, admin_sidebar_open)
        │
        ▼
2. st.set_page_config()  ← WAJIB PALING AWAL
        │
        ▼
3. st.markdown(COMMON_CSS)  ← inject font + shared CSS
        │
        ▼
4. st.markdown("<style>nav bar CSS</style>")  ← inline CSS kritis
        │
        ▼
5. check_admin_login()  ← redirect ke Beranda jika belum login
        │
        ▼
6. st.markdown("<div class='sara-nav-bar'>...</div>")  ← render nav bar
        │
        ▼
7. with st.sidebar:  ← isi sidebar (nav, filter)
        │
        ▼
8. Konten utama halaman (KPI, chart, tabel, chat, dll.)
        │
        ▼
        Selesai satu siklus render
        ↓ (menunggu interaksi user)
        ↑ (klik/input → rerun dari awal lagi)
```

### Aturan Penting

| Aturan | Alasan |
|---|---|
| `st.set_page_config()` selalu di baris pertama setelah import | Streamlit error jika ada output sebelumnya |
| Baca session state SEBELUM `set_page_config()` | Satu-satunya cara mengontrol `initial_sidebar_state` secara dinamis |
| CSS kritis (nav bar, FAB) di-inject inline, bukan di COMMON_CSS | Module `utils.py` bisa di-cache bytecode; inline selalu fresh |
| `st.rerun()` setelah ubah session state | Streamlit tidak langsung re-render; perlu dipaksa |

---

## Ringkasan Visual

```
┌────────────────────────── Sara Nusantara ────────────────────────────┐
│                                                                      │
│  FONT: Outfit (heading) + Inter (body) + Material Symbols (icons)   │
│                                                                      │
│  WARNA: #FF6B35 (aksen) · #2D2522 (teks) · #FFFBF8 (surface)       │
│                                                                      │
│  CSS: config.toml → main.css / COMMON_CSS → inline per halaman      │
│                                                                      │
│  HALAMAN:                                                            │
│  ├── Beranda.py         → chat publik + login popover               │
│  ├── 1_Dashboard...     → KPI cards + Plotly charts (admin)         │
│  └── 2_Reservation...   → tabel + detail panel (admin)              │
│                                                                      │
│  KOMPONEN BERSAMA: nav bar · sidebar FAB · kpi-card · section-title │
│                    badge · back-button · sara-nav-chip               │
└──────────────────────────────────────────────────────────────────────┘
```

---

*Dokumen ini disiapkan untuk keperluan presentasi Capstone Project.*
*Kelompok 3 – CAMP Batch 4 · Hana Jatmiana · 2026*
