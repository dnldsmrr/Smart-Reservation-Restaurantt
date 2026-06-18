# Panduan Frontend – Sara Nusantara

Dokumen ini menjelaskan cara Streamlit membangun tampilan UI dan bagaimana CSS diterapkan di project ini. Ditulis untuk anggota tim yang baru mengenal Python dan Streamlit.

---

## 1. Cara Streamlit Membangun Tampilan

### Konsep Dasar: Kode Python = Tampilan



Di Streamlit, kamu tidak menulis HTML secara langsung seperti di website biasa. Setiap baris Python yang kamu tulis langsung menghasilkan elemen di halaman.

```python
st.title("Halo Dunia")          # → muncul judul besar
st.write("Ini teks biasa")      # → muncul paragraf
st.button("Klik Saya")          # → muncul tombol

st.button("Klik Saya")          # → muncul tombol
```

Setiap kali pengguna mengklik sesuatu atau mengisi form, Streamlit **menjalankan ulang seluruh script dari atas ke bawah**. Ini disebut "rerun". Jadi urutan kode = urutan tampilan di halaman.

---

### Widget Utama yang Dipakai di Project Ini

| Kode Python | Hasil di Halaman |
|---|---|
| `st.title("teks")` | Judul besar |
| `st.markdown("teks")` | Teks dengan format Markdown / HTML |
| `st.button("label")` | Tombol yang bisa diklik |
| `st.text_input("label")` | Kolom isi teks |
| `st.selectbox("label", pilihan)` | Dropdown pilihan |
| `st.multiselect("label", pilihan)` | Dropdown pilihan ganda |
| `st.columns([1, 2, 1])` | Bagi halaman jadi beberapa kolom |
| `st.sidebar` | Semua yang masuk ke panel kiri |
| `st.chat_input("placeholder")` | Kolom chat di bawah halaman |
| `st.chat_message("role")` | Balon chat (user / assistant) |
| `st.popover("label")` | Panel popup kecil |
| `st.page_link("file.py")` | Link navigasi ke halaman lain |
| `st.toast("pesan")` | Notifikasi kecil di pojok |

---

### Layout: Kolom dan Sidebar

**Kolom** membagi halaman secara horizontal:

```python
col1, col2, col3 = st.columns(3)       # 3 kolom sama lebar

with col1:
    st.metric("Total", 508)            # konten masuk kolom 1

with col2:
    st.metric("Revenue", "Rp510Jt")    # konten masuk kolom 2
```

Di project ini dipakai untuk KPI cards di Dashboard Analytics.

**Sidebar** adalah panel kiri yang bisa disembunyikan:

```python
with st.sidebar:
    st.markdown("## Menu")
    st.page_link("Beranda.py", label="Chat")
    st.button("Keluar Admin")
```

---

### Session State: Menyimpan Data Antar Klik

Karena Streamlit re-run setiap kali ada interaksi, kamu perlu tempat menyimpan data yang tidak hilang saat re-run. Itulah `st.session_state`.

```python
# Inisialisasi (cukup sekali, pakai pengecekan)
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# Baca nilainya
if st.session_state.admin_logged_in:
    st.write("Selamat datang, Admin!")

# Ubah nilainya (misalnya saat tombol diklik)
if st.button("Login"):
    st.session_state.admin_logged_in = True
    st.rerun()   # paksa re-run agar tampilan langsung update
```

Di project ini `session_state` dipakai untuk:
- `admin_logged_in` → apakah admin sudah login
- `admin_sidebar_open` → apakah sidebar terbuka atau tersembunyi
- `messages` → riwayat percakapan chatbot

---

### Multipage: File di Folder `pages/`

Streamlit otomatis membuat navigasi dari file `.py` di folder `pages/`. Nama file menentukan urutan dan nama halaman:

```
pages/
├── 1_Dashboard_Analytics.py    → /Dashboard_Analytics
└── 2_Reservation_Management.py → /Reservation_Management
```

Angka di depan (`1_`, `2_`) menentukan urutan. Navigasi antar halaman pakai:

```python
st.switch_page("pages/1_Dashboard_Analytics.py")   # pindah halaman via kode
st.page_link("Beranda.py", label="Kembali")        # link yang bisa diklik user
```

Di project ini, navigasi otomatis Streamlit **dimatikan** (`showSidebarNavigation = false` di `.streamlit/config.toml`), dan diganti dengan nav bar buatan sendiri.

---

## 2. Cara Pakai CSS di Streamlit

### Masalahnya: Streamlit Punya Gaya Sendiri

Streamlit sudah punya tampilan bawaan. Kalau kamu mau ubah warna, font, ukuran, atau posisi, kamu perlu "menimpa" gaya bawaannya dengan CSS kamu sendiri.

---

### Cara 1 – `st.markdown()` dengan HTML/CSS

Ini cara paling sering dipakai di project ini. Kamu tulis tag `<style>` di dalam string Python, lalu inject ke halaman.

```python
st.markdown("""
<style>
/* Ubah warna background halaman */
.stApp {
    background-color: #F4F4F4 !important;
}

/* Ubah semua tombol jadi oranye */
.stButton > button {
    background: #FF6B35 !important;
    color: white !important;
    border-radius: 20px !important;
}
</style>
""", unsafe_allow_html=True)
```

> **Wajib**: tambahkan `unsafe_allow_html=True` di parameter. Tanpa itu, HTML/CSS tidak akan dirender.

---

### Cara 2 – File CSS Eksternal

CSS bisa juga disimpan di file `.css` tersendiri, lalu di-load lewat fungsi `load_css()` dari `utils.py`:

```python
from utils import load_css
load_css("main.css")   # akan membaca styles/main.css dan inject ke halaman
```

Di project ini `styles/main.css` dipakai khusus untuk halaman chat (Beranda).

---

### Cara 3 – CSS di `utils.py` (COMMON_CSS)

CSS yang dipakai di **banyak halaman** disimpan sebagai string di variabel `COMMON_CSS` dalam `utils.py`:

```python
# Di utils.py
COMMON_CSS = """
<style>
.kpi-card { background: white; border-radius: 14px; ... }
.section-title { font-family: 'Outfit', sans-serif; ... }
</style>
"""
```

Lalu di setiap halaman admin:

```python
from utils import COMMON_CSS
st.markdown(COMMON_CSS, unsafe_allow_html=True)
```

Ini seperti "stylesheet bersama" yang berlaku di semua halaman admin.

---

### Cara 4 – Tema via `.streamlit/config.toml`

Untuk warna dan font dasar, Streamlit punya file konfigurasi tema:

```toml
# .streamlit/config.toml
[theme]
primaryColor     = "#FF6B35"   # warna aksen utama (tombol, link, dll)
backgroundColor  = "#F4F4F8"   # background halaman
textColor        = "#2D2522"   # warna teks
```

Ini berlaku global untuk semua halaman, tapi bisa ditimpa oleh CSS manual.

---

## 3. Selector CSS untuk Elemen Streamlit

Streamlit menggunakan React di balik layar dan menghasilkan HTML dengan class dan `data-testid` tertentu. Berikut selector yang paling sering dipakai:

### Elemen Utama

| Yang Ingin Diubah | Selector CSS |
|---|---|
| Background seluruh app | `.stApp` |
| Area konten utama | `.main .block-container` |
| Panel sidebar | `section[data-testid="stSidebar"]` |
| Header Streamlit (transparan) | `header[data-testid="stHeader"]` |
| Semua tombol | `.stButton > button` |
| Tombol form submit | `[data-testid="stFormSubmitButton"] > button` |
| Kolom input chat | `div[data-testid="stChatInput"]` |
| Balon pesan chat | `div[data-testid="stChatMessage"]` |
| Container markdown | `div[data-testid="stMarkdownContainer"]` |

### Contoh Nyata dari Project Ini

```css
/* Sembunyikan toolbar Streamlit (deploy button, dll) */
[data-testid="stToolbar"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; }
footer { display: none !important; }

/* Chat input jadi rounded pill */
div[data-testid="stChatInput"] {
    border-radius: 28px !important;
    max-width: 800px !important;
    margin: 0 auto !important;
}

/* Balon chat user (kanan, oranye) */
div[data-testid="stChatMessage"]:has(svg[data-testid="chatAvatarIcon-user"])
div[data-testid="stChatMessageContent"] {
    background-color: #FF6B35 !important;
    border-radius: 18px 4px 18px 18px !important;
    margin-left: auto !important;
}
```

---

## 4. Teknik Khusus di Project Ini

### Mengapa `!important` Banyak Dipakai

Streamlit punya gaya bawaan dengan spesifisitas tinggi (pakai emotion CSS-in-JS). Untuk menimpanya, hampir semua aturan CSS kustom perlu ditambah `!important`:

```css
/* Tanpa !important → tidak efek */
.stButton > button { background: orange; }

/* Dengan !important → berhasil menimpa */
.stButton > button { background: orange !important; }
```

---

### HTML Murni untuk Elemen Non-Interaktif

Nav bar di bagian atas halaman tidak bisa menggunakan widget Streamlit karena ada masalah teknis dengan `position: fixed`. Solusinya: render sebagai HTML murni via `st.markdown()`:

```python
st.markdown(f"""
<div style="position:fixed; top:0; left:0; right:0; height:72px;
            background:white; z-index:999998; display:flex;
            align-items:center; padding:0 2rem;">
    <img src="data:image/png;base64,{logo_b64}" style="width:44px;">
    <strong style="margin-left:14px; font-family:'Outfit';">Sara Nusantara</strong>
</div>
""", unsafe_allow_html=True)
```

> HTML murni hanya untuk elemen yang **tidak butuh interaksi** (tidak ada tombol klik). Untuk elemen interaktif tetap pakai widget Streamlit.

---

### Inline Style vs CSS Class

**Inline style** (langsung di tag HTML) cocok untuk satu elemen spesifik:

```python
st.markdown("""
<div style="background:#FF6B35; color:white; padding:20px; border-radius:12px;">
    Dashboard Analytics
</div>
""", unsafe_allow_html=True)
```

**CSS class** (di blok `<style>`) lebih baik kalau dipakai berulang:

```python
st.markdown("""
<style>
.header-card {
    background: #FF6B35;
    color: white;
    padding: 20px;
    border-radius: 12px;
}
</style>

<div class="header-card">Dashboard Analytics</div>
<div class="header-card">Manajemen Reservasi</div>
""", unsafe_allow_html=True)
```

---

### Menggunakan F-String untuk Warna Dinamis

Karena warna disimpan sebagai konstanta di `utils.py`, kita pakai f-string Python supaya tidak perlu hardcode hex di CSS:

```python
from utils import GOLD, DARK, CREAM

st.markdown(f"""
<style>
.my-button {{                   /* ← kurung kurawal di f-string harus dobel {{ }} */
    background: {GOLD};         /* ← nilai dari variabel Python */
    color: {DARK};
}}
</style>
""", unsafe_allow_html=True)
```

> Perhatikan: di dalam f-string, kurung kurawal CSS harus ditulis **dobel** (`{{` dan `}}`) agar Python tidak mengiranya sebagai variabel.

---

### Icons: Material Symbols

Semua icon di project ini menggunakan Google Material Symbols. Ada dua cara pakainya:

**Cara A – Untuk widget Streamlit** (tombol, page_link, dll):
```python
st.button("Keluar", icon=":material/logout:")
st.page_link("Beranda.py", icon=":material/chat:")
```

**Cara B – Untuk konten HTML** (di dalam `st.markdown`):
```python
st.markdown("""
<span class="material-symbols-outlined"
      style="font-size:1.5rem; color:#FF6B35; vertical-align:middle;">
    bar_chart
</span>
Dashboard Analytics
""", unsafe_allow_html=True)
```

Font CDN-nya sudah di-import di COMMON_CSS:
```css
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:...');
```

Cari nama icon di: **fonts.google.com/icons**

---

## 5. Struktur CSS di Project Ini

```
Halaman Chat (Beranda.py)
└── styles/main.css           ← background, chat balloon, chat input, nav bar

Halaman Admin
├── utils.py → COMMON_CSS     ← font, sidebar, tombol, kpi-card, section-title
├── Inline per halaman        ← fine-tuning spesifik (header card, tabel, dll)
└── Inline nav bar CSS        ← .sara-nav-bar, .sara-nav-chip, padding-top
```

**Urutan prioritas** (dari tertinggi ke terendah):
1. Inline `style=""` langsung di tag HTML
2. CSS class dengan `!important` yang paling spesifik (lebih banyak selector = lebih spesifik)
3. Gaya bawaan Streamlit (emotion CSS)

---

## 6. Checklist Kalau Mau Ubah Tampilan

| Tujuan | Caranya |
|---|---|
| Ubah warna tombol di semua halaman admin | Edit `.stButton > button` di `COMMON_CSS` (`utils.py`) |
| Ubah tampilan chat balloon | Edit `styles/main.css` |
| Ubah nav bar (logo, teks) | Edit blok `st.markdown(f"""<div class="sara-nav-bar">...""")` di tiap halaman |
| Tambah warna baru | Tambah konstanta di `utils.py`, import di halaman yang butuh |
| Ubah tema dasar (warna primary) | Edit `.streamlit/config.toml` |
| Sembunyikan elemen Streamlit | Tambah `display: none !important` di selector yang sesuai |

---

*Dokumen ini ditulis untuk Kelompok 3 – CAMP Batch 4 · 2026*
