import streamlit as st
import uuid
import base64
import os
import re
import urllib.request
import json
import pandas as pd
from utils import load_data, append_reservation, load_css, check_admin_login, GOLD, DARK, CREAM
from dotenv import load_dotenv

# ─────────────────── PAGE CONFIG ───────────────────
st.set_page_config(
    page_title="Sara Nusantara — AI Reservation Assistant",
    page_icon=":material/restaurant:",
    layout="centered",
    initial_sidebar_state="auto",
)

# ─────────────────── LOGO B64 HELPER ───────────────────
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except:
        return ""

logo_path = os.path.join(os.path.dirname(__file__), "assets", "sara_logo.png")
logo_b64 = get_base64_image(logo_path)
LOGO_IMG_TAG = (
    f'<img src="data:image/png;base64,{logo_b64}" '
    f'style="width: 44px; height: 44px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.06); object-fit: cover;">'
    if logo_b64 else '<div style="width:44px;height:44px;background:#EAEAEA;border-radius:10px;"></div>'
)

# ─────────────────── SESSION STATE ───────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# Load external stylesheets
load_css("main.css")

# Extra styles injected after main.css
st.markdown(f"""
<style>
/* Admin sidebar buttons - orange gradient */
section[data-testid="stSidebar"] .stButton > button {{
    border-radius: 999px !important;
    border: none !important;
    background: linear-gradient(135deg, #FF6B35, #FF8E66) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 14px rgba(255,107,53,0.18) !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}}

/* Fixed full-width top nav bar (pure HTML) */
.sara-nav-bar {{
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 72px;
    z-index: 999998;
    background: #FFFFFF;
    border-bottom: 1px solid #EAEAEA;
    padding: 0 2rem;
    box-sizing: border-box;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
}}
.sara-nav-chip {{
    background: {CREAM};
    color: {GOLD};
    border: 1px solid #FFE0D3;
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    white-space: nowrap;
}}

/* Masuk / Admin popover — fixed at top-right, aligned with nav */
div[data-testid="stPopover"] {{
    position: fixed !important;
    top: 14px !important;
    right: 2rem !important;
    z-index: 9999999 !important;
    width: auto !important;
}}
div[data-testid="stPopover"] > button {{
    border-radius: 20px !important;
    background: #FF6B35 !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 8px 20px !important;
    box-shadow: 0 2px 8px rgba(255,107,53,0.22) !important;
}}
div[data-testid="stPopover"] > button:hover {{
    background: #E55A2B !important;
    opacity: 1 !important;
}}

/* Offset page content below fixed nav + leave room for Masuk button */
.block-container {{
    padding-top: 86px !important;
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────── TOP NAV (pure HTML — no widgets inside) ───────────────────
st.markdown(f"""
<div class="sara-nav-bar">
    <div style="display:flex;align-items:center;gap:14px;">
        {LOGO_IMG_TAG}
        <div>
            <div style="font-weight:800;font-size:18px;color:{DARK};
                 font-family:'Outfit',sans-serif;letter-spacing:-0.3px;line-height:1.1;">
                Sara Nusantara
            </div>
            <div style="font-size:11px;color:#8E8E8E;margin-top:3px;
                 display:flex;align-items:center;gap:5px;">
                <span style="color:#28A745;font-size:9px;">●</span>
                Online · AI Reservation Assistant
            </div>
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:10px;padding-right:160px;">
        <span class="sara-nav-chip">Sara Nusantara</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────── MASUK / ADMIN BUTTON (fixed top-right via CSS) ───────────────────
if not st.session_state.admin_logged_in:
    with st.popover("Masuk"):
        st.markdown("**Verifikasi Admin**")
        with st.form("beranda_login_form", clear_on_submit=True):
            pass_input = st.text_input("Kata Sandi", type="password",
                label_visibility="collapsed", placeholder="Sandi...")
            submitted = st.form_submit_button("Verifikasi", use_container_width=True)
        if submitted:
            if pass_input == "admin123":
                st.session_state.admin_logged_in = True
                st.switch_page("pages/1_Dashboard_Analytics.py")
            else:
                st.error("Sandi salah!")
else:
    with st.popover(":material/manage_accounts: Admin"):
        if st.button("Keluar Admin", icon=":material/logout:", use_container_width=True,
                     key="nav_logout"):
            st.session_state.admin_logged_in = False
            st.toast("Admin keluar.")
            st.rerun()

# ─────────────────── SIDEBAR ───────────────────
if st.session_state.admin_logged_in:
    with st.sidebar:
        st.markdown("<h3 style='margin-top:0; padding-top:0; color:#FF6B35;'>Sara Nusantara</h3>", unsafe_allow_html=True)
        st.write("Sistem manajemen reservasi Mandala Rasa.")
        st.markdown("---")
        st.page_link("Beranda.py", label="Halaman Chat Utama", icon=":material/chat:")
        st.page_link("pages/1_Dashboard_Analytics.py", label="Dashboard Analytics", icon=":material/bar_chart:")
        st.page_link("pages/2_Reservation_Management.py", label="Kelola Reservasi", icon=":material/table_chart:")
        st.markdown("---")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Percakapan Baru", icon=":material/refresh:", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Keluar Admin", icon=":material/logout:", use_container_width=True, key="beranda_sidebar_logout"):
            st.session_state.admin_logged_in = False
            st.toast("Admin keluar.")
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption(f"Session: `{st.session_state.session_id[:8]}...`")
else:
    # Non-admin: completely hide sidebar and its toggle (no ghost space)
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        button[data-testid="collapsedControl"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ─────────────────── DATA & CONSTANTS ───────────────────
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
df_reservasi = load_data()

RESTAURANT_INFO = {
    "nama": "Mandala Rasa",
    "jam_operasional": "Senin–Minggu, 10:00–22:00 WIB",
    "area": ["Indoor", "Outdoor", "Garden", "Bar Area", "VIP Room", "Private Room"],
    "fasilitas": ["WiFi gratis", "Area parkir luas", "Smoking area terpisah",
                  "Live music Jumat–Sabtu mulai 19:00",
                  "Private room untuk acara eksklusif",
                  "Aksesibel untuk pengguna kursi roda"],
    "kebijakan": [
        "Reservasi dibuat min. 2 jam sebelum kedatangan",
        "Pembatalan gratis jika dilakukan H-1",
        "No-show 3x akan masuk daftar blacklist",
        "Deposit 50% untuk VIP Room & Private Room",
        "Hewan peliharaan tidak diizinkan masuk",
    ],
    "menu_unggulan": ["Sate Maranggi Spesial", "Nasi Goreng Wagyu",
                      "Premium Grill Platter", "Signature Mocktail"],
    "kapasitas": {"Indoor": 80, "Outdoor": 60, "Garden": 80,
                  "Bar Area": 40, "VIP Room": 60, "Private Room": 120},
}

SYSTEM_PROMPT = """Kamu adalah AI Reservation Assistant bernama "Sara Nusantara" untuk restoran Mandala Rasa.
Kamu berbicara dalam Bahasa Indonesia yang ramah, hangat, dan profesional.

Tugas utamamu:
1. MEMBUAT RESERVASI — Kumpulkan: nama, jumlah orang, tanggal, waktu, area pilihan, occasion, special request. Konfirmasi semua detail sebelum memproses.
2. CEK RESERVASI — Minta nama lengkap atau ID reservasi, lalu tampilkan detail.
3. INFO RESTORAN — Jawab pertanyaan seputar jam operasional, area, fasilitas, kebijakan, menu.

Info Restoran Mandala Rasa:
- Jam: Senin–Minggu 10:00–22:00 WIB (tidak tutup hari libur nasional kecuali Lebaran)
- Area: Indoor (80 pax), Outdoor (60), Garden (80), Bar Area (40), VIP Room (60), Private Room (120)
- Fasilitas: WiFi gratis, Parkir luas, Smoking area, Live music Jum–Sab 19:00, Aksesibel kursi roda
- Kebijakan: Reservasi min 2 jam sebelumnya. Batal gratis H-1. No-show 3x → blacklist. Deposit 50% untuk VIP/Private.
- Menu andalan: Sate Maranggi Spesial, Nasi Goreng Wagyu, Premium Grill Platter, Signature Mocktail

Panduan menjawab:
- Gunakan bahasa yang ramah, hangat, dan profesional tanpa emoji
- Jika ada info yang kurang untuk reservasi, tanya dengan sopan
- Berikan jawaban yang terstruktur dan mudah dibaca
- Akhiri setiap percakapan dengan tawaran bantuan lanjutan"""

# ─────────────────── TOOLS ───────────────────
def cek_reservasi_tool(query: str) -> dict:
    q = query.strip().lower()
    mask = (
        df_reservasi["Nama Customer"].str.lower().str.contains(q, na=False) |
        df_reservasi["Reservation ID"].str.lower().str.contains(q, na=False) |
        df_reservasi["Customer ID"].str.lower().str.contains(q, na=False)
    )
    result = df_reservasi[mask].head(3)
    if result.empty:
        return {"found": False}
    rows = []
    for _, r in result.iterrows():
        rows.append({
            "id": r["Reservation ID"], "nama": r["Nama Customer"],
            "tanggal": str(r["Tanggal"]), "waktu": str(r["Waktu Reservasi"]),
            "area": r["Area Meja"], "pax": int(r["Jumlah Orang"]),
            "status": r["Status Reservasi"], "occasion": r["Occasion"],
        })
    return {"found": True, "reservations": rows}


def find_reservation_by_id(reservation_id: str) -> dict:
    query = reservation_id.strip()
    if not query:
        return {"found": False, "error": "Masukkan ID reservasi terlebih dahulu."}
    return cek_reservasi_tool(query)


def render_reservation_detail(reservation: dict) -> str:
    return (
        f"**ID Reservasi:** `{reservation['id']}`\n"
        f"**Nama:** {reservation['nama']}\n"
        f"**Tanggal:** {reservation['tanggal']} pukul {reservation['waktu']}\n"
        f"**Area:** {reservation['area']}\n"
        f"**Jumlah Orang:** {reservation['pax']}\n"
        f"**Occasion:** {reservation['occasion']}\n"
        f"**Status:** {reservation['status']}"
    )


def buat_reservasi_tool(nama, pax, tanggal, waktu,
                        area="Indoor", occasion="Casual Dining",
                        special_request="Tidak ada", phone=None, email=None, duration=None):
    import random
    new_id = f"RSV{random.randint(10000, 99999):05d}"
    customer_id = f"CUST{random.randint(1000, 9999):04d}"
    duration = duration or 120
    table_size = max(2, min(pax, 12))
    table_type = f"Meja {table_size} Orang"
    table_number = random.randint(1, 60)
    est_budget = 150000
    total_estimasi = pax * est_budget

    record = {
        "Reservation ID": new_id,
        "Customer ID": customer_id,
        "Nama Customer": nama,
        "No. HP": phone or "",
        "Email": email or "",
        "Tanggal Reservasi": tanggal,
        "Waktu Reservasi": waktu,
        "Durasi (menit)": duration,
        "Jumlah Orang": pax,
        "Area Meja": area,
        "Tipe Meja": table_type,
        "Nomor Meja": table_number,
        "Occasion": occasion,
        "Special Request": special_request,
        "Estimasi Budget/Orang (IDR)": est_budget,
        "Total Estimasi (IDR)": total_estimasi,
        "Metode Pembayaran": "Onsite",
        "Channel Booking": "AI Assistant",
        "Status Reservasi": "Confirmed",
        "Rating": None,
        "Catatan Staff": None,
        "Tanggal": tanggal,
        "Bulan": int(tanggal.split("-")[1]) if len(tanggal.split("-")) >= 2 else None,
    }

    result = append_reservation(record)
    if not result.get("success", False):
        return {
            "success": False,
            "error": result.get("error", "Gagal menyimpan reservasi lokal."),
        }

    warning_msg = result.get("warning")
    global df_reservasi
    new_row = pd.DataFrame([record])
    new_row["Tanggal Reservasi"] = pd.to_datetime(new_row["Tanggal Reservasi"])
    df_reservasi = pd.concat([df_reservasi, new_row], ignore_index=True)

    output = {
        "success": True, "reservation_id": new_id,
        "detail": {"nama": nama, "pax": pax, "tanggal": tanggal,
                   "waktu": waktu, "area": area, "occasion": occasion,
                   "special_request": special_request, "status": "Confirmed"},
    }
    if warning_msg:
        output["warning"] = warning_msg
    return output

# ─────────────────── GEMINI CALL ───────────────────
def call_gemini(messages: list) -> str:
    import urllib.request, json as jm, traceback

    url = ("https://generativelanguage.googleapis.com/v1beta/"
           "models/gemini-2.5-flash-lite:generateContent"
           f"?key={GEMINI_API_KEY}")

    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        if contents and contents[-1]["role"] == role:
            contents[-1]["parts"][0]["text"] += "\n" + m["content"]
        else:
            contents.append({"role": role, "parts": [{"text": m["content"]}]})

    if contents and contents[0]["role"] == "model":
        contents = contents[1:]

    payload = jm.dumps({
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.75,
            "maxOutputTokens": 1024,
            "topP": 0.9,
        }
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = jm.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return f"Gemini API error {e.code}: {body[:200]}"
    except Exception:
        return traceback.format_exc(limit=2)

# ─────────────────── HEURISTIC FALLBACK ───────────────────
def detect_intent(msg):
    m = msg.lower()
    if any(k in m for k in ["reservasi","pesan","booking","book","mau makan",
                             "ingin makan","duduk","meja"]):
        return "buat_reservasi"
    if any(k in m for k in ["cek","status","check","konfirmasi","lihat reservasi"]):
        return "cek_reservasi"
    if any(k in m for k in ["jam","buka","tutup","area","fasilitas","kebijakan",
                             "info","menu","parkir","wifi","kapasitas"]):
        return "info_restoran"
    if any(k in m for k in ["halo","hai","hello","hi","selamat","assalamualaikum",
                             "apa kabar","good morning","good evening"]):
        return "greeting"
    return "general"

def extract_params(msg):
    params = {}
    nm = re.search(r"(?:nama|atas nama|an\.?)\s+([A-Za-z][a-zA-Z\s]{2,30})",
                   msg, re.IGNORECASE)
    if nm: params["nama"] = nm.group(1).strip()
    px = re.search(r"(\d+)\s*(?:orang|pax|tamu|person|guests?)", msg, re.IGNORECASE)
    if px: params["pax"] = int(px.group(1))
    dt = re.search(r"(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{2,4}))?", msg)
    if dt:
        d,mo = dt.group(1), dt.group(2)
        yr = dt.group(3) or "2025"
        yr = yr if len(yr)==4 else "20"+yr
        params["tanggal"] = f"{yr}-{mo.zfill(2)}-{d.zfill(2)}"
    tm = re.search(r"(\d{1,2})[:\.](\d{2})\s*(?:WIB)?|pukul\s+(\d{1,2})[:\.]?(\d{0,2})",
                   msg, re.IGNORECASE)
    if tm:
        h = tm.group(3) or tm.group(1)
        mn = tm.group(4) or tm.group(2) or "00"
        params["waktu"] = f"{h.zfill(2)}:{mn.zfill(2)}"
    # phone number (simple international/local patterns)
    ph = re.search(r"(\+62|62|0)\s*[-.]?\s*(\d{2,4})[\s\-\.]*\d{4,8}", msg)
    if ph:
        # normalize basic formatting
        digits = re.sub(r"[^0-9+]", "", ph.group(0))
        params["phone"] = digits
    # email
    em = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", msg)
    if em:
        params["email"] = em.group(0)
    # duration (minutes or hours)
    dur = re.search(r"(durasi|lama).*?(\d+)\s*(menit|min|mnt)|(\d+)\s*menit|(\d+)\s*jam", msg, re.IGNORECASE)
    if dur:
        if dur.group(2):
            params["duration"] = int(dur.group(2))
        elif dur.group(4):
            params["duration"] = int(dur.group(4))
        elif dur.group(5):
            params["duration"] = int(dur.group(5)) * 60
    for a in RESTAURANT_INFO["area"]:
        if a.lower() in msg.lower(): params["area"] = a; break
    occ_map = {"birthday":"Birthday","ulang tahun":"Birthday",
               "anniversary":"Anniversary","bisnis":"Business Meeting",
               "meeting":"Business Meeting","rapat":"Business Meeting",
               "romantis":"Date Night","date":"Date Night",
               "keluarga":"Family Gathering","family":"Family Gathering",
               "arisan":"Arisan","wisuda":"Wisuda","lamaran":"Lamaran"}
    for k,v in occ_map.items():
        if k in msg.lower(): params["occasion"] = v; break
    return params

def heuristic_response(msg):
    intent = detect_intent(msg)
    params = extract_params(msg)

    if intent == "greeting":
        return ("Halo! Selamat datang di **Mandala Rasa**\n\n"
                "Saya **Sara Nusantara**, asisten reservasi Anda. Ada yang bisa saya bantu?\n\n"
                "**Buat reservasi** — pesan meja untuk kunjungan Anda\n\n"
                "**Cek reservasi** — lihat detail & status reservasi\n\n"
                "**Info restoran** — jam buka, area, fasilitas, kebijakan")

    if intent == "cek_reservasi":
        q = re.sub(r"(cek|status|check|reservasi|detail|atas nama|nama)\s*",
                   "", msg, flags=re.IGNORECASE).strip()
        if not q or len(q) < 2:
            return "Silakan sebutkan **nama lengkap** atau **ID reservasi** Anda.\nContoh: *cek reservasi atas nama Budi*"
        result = cek_reservasi_tool(q)
        if not result["found"]:
            return (f"Maaf, reservasi atas nama atau ID **\"{q}\"** tidak ditemukan.\n\n"
                    "Pastikan penulisan nama sudah benar, atau coba masukkan ID reservasi "
                    "yang tertera di konfirmasi Anda, contoh: `RSV00001`.")
        rows = result["reservations"]
        label = "reservasi" if len(rows) == 1 else "reservasi"
        resp = f"Ditemukan **{len(rows)} {label}** atas nama **{q}**:\n\n"
        for i, r in enumerate(rows):
            resp += (f"**{r['id']}**  \n"
                     f"Nama: {r['nama']}  \n"
                     f"Tanggal: {r['tanggal']} pukul {r['waktu']}  \n"
                     f"Tamu: {r['pax']} orang — Area: {r['area']}  \n"
                     f"Occasion: {r['occasion']}  \n"
                     f"Status: **{r['status']}**")
            if i < len(rows) - 1:
                resp += "\n\n---\n\n"
        return resp

    if intent == "buat_reservasi":
        missing = []
        if "nama"    not in params: missing.append("nama Anda")
        if "pax"     not in params: missing.append("jumlah tamu")
        if "tanggal" not in params: missing.append("tanggal (format DD/MM)")
        if "waktu"   not in params: missing.append("waktu (contoh: 19:00)")
        if "phone"   not in params: missing.append("nomor telepon")
        if "duration" not in params: missing.append("durasi kedatangan (menit)")
        if missing:
            missing_list = "\n\n".join(f"**{m}**" for m in missing)
            return ("Saya siap membantu reservasi Anda!\n\n"
                    "Mohon lengkapi informasi berikut:\n\n"
                    + missing_list
                    + "\n\n*Contoh: Reservasi atas nama Sinta, 4 orang, "
                      "20/07, jam 19:00, area Garden, untuk anniversary*")
        allowed = ["nama","pax","tanggal","waktu","area","occasion","phone","email","duration"]
        result = buat_reservasi_tool(**{k: params[k] for k in params if k in allowed})
        if not result.get("success", False):
            return (f"Maaf, terjadi masalah saat menyimpan reservasi:\n"
                    f"{result.get('error', 'Terjadi kesalahan tak terduga')}\n\n"
                    "Silakan coba kembali atau hubungi admin.")

        d = result["detail"]
        warning_msg = result.get("warning")
        response = (f"Reservasi Anda telah berhasil dikonfirmasi!\n\n"
                    f"**ID Reservasi:** `{result['reservation_id']}`  \n"
                    f"**Nama:** {d['nama']}  \n"
                    f"**Jumlah Tamu:** {d['pax']} orang  \n"
                    f"**Tanggal:** {d['tanggal']} pukul {d['waktu']}  \n"
                    f"**Area:** {d['area']}  \n"
                    f"**Occasion:** {d['occasion']}  \n"
                    f"**Status:** Confirmed\n\n"
                    "Harap simpan ID reservasi Anda. Tim kami akan menghubungi melalui WhatsApp untuk konfirmasi lebih lanjut.")
        if warning_msg:
            response += (f"\n\nCatatan: {warning_msg}\n"
                         "Data tetap tersimpan secara lokal.")
        return response

    if intent == "info_restoran":
        m = msg.lower()
        info = RESTAURANT_INFO
        if any(k in m for k in ["jam","buka","tutup","operasional"]):
            return (f"**Jam Operasional Mandala Rasa:**\n\n"
                    f"**{info['jam_operasional']}**\n\n"
                    "Kami buka setiap hari, termasuk hari libur nasional "
                    "(kecuali Lebaran Hari H).")
        if any(k in m for k in ["area","meja","tempat","duduk","vip","private","kapasitas"]):
            areas = "\n".join(f"• **{a}** — kapasitas ±{info['kapasitas'].get(a,'?')} orang"
                              for a in info["area"])
            return f"**Area yang Tersedia di Mandala Rasa:**\n\n{areas}"
        if any(k in m for k in ["fasilitas","wifi","parkir","musik","aksesibel","smoking"]):
            fac = "\n".join(f"• {f}" for f in info["fasilitas"])
            return f"**Fasilitas Mandala Rasa:**\n\n{fac}"
        if any(k in m for k in ["kebijakan","aturan","deposit","cancel","batal","no-show"]):
            pol = "\n".join(f"• {p}" for p in info["kebijakan"])
            return f"**Kebijakan Reservasi:**\n\n{pol}"
        if any(k in m for k in ["menu","makanan","minuman","rekomendasi","recommend"]):
            men = "\n".join(f"• {m2}" for m2 in info["menu_unggulan"])
            return (f"**Menu Andalan Mandala Rasa:**\n\n{men}\n\n"
                    "Untuk daftar menu lengkap, silakan kunjungi meja kami "
                    "atau minta dari staf saat kedatangan.")
        return (f"**Mandala Rasa — Info Singkat:**\n\n"
                f"Jam: {info['jam_operasional']}\n"
                f"Area: {', '.join(info['area'])}\n"
                f"Fasilitas: WiFi · Parkir · Live Music (Jum-Sab)\n\n"
                "Tanya lebih lanjut tentang: *jam buka*, *area meja*, "
                "*fasilitas*, atau *kebijakan*?")

    return ("Hmm, saya belum sepenuhnya memahami permintaan Anda.\n\n"
            "Saya bisa membantu dengan:\n\n"
            "**Buat reservasi** — *Reservasi 4 orang, 20 Juli, jam 19:00*\n\n"
            "**Cek reservasi** — *Cek reservasi atas nama Andi*\n\n"
            "**Info restoran** — *Jam buka berapa? Ada WiFi?*\n\n"
            "Silakan coba lagi dengan kalimat yang lebih spesifik.")

def process_user_message(user_input: str) -> str:
    reply = heuristic_response(user_input.strip())
    if reply.startswith("Hmm, saya belum sepenuhnya memahami permintaan Anda"):
        return call_gemini(st.session_state.messages + [{"role": "user", "content": user_input.strip()}])
    return reply

# ─────────────────── CHAT ACTIONS ───────────────────
prompt = st.chat_input("Tanya Sara Nusantara sesuatu...")

if st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    assistant_response = process_user_message(prompt)
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

# ─────────────────── CHAT DISPLAY ┋─
if not st.session_state.messages:
    # Large centered greeting
    st.markdown(
        """
        <div style="text-align: center; margin-top: 14vh; margin-bottom: 6vh;">
            <h1 style="font-size: 36px; font-weight: 700; color: #2D2522; font-family: 'Outfit', sans-serif; letter-spacing: -1px; margin-bottom: 10px;">
                Ada yang bisa Sara bantu?
            </h1>
            <p style="color: #666; font-size: 16px; font-family: 'Inter', sans-serif;">
                Silakan pilih opsi cepat di bawah atau kirim pesan baru untuk memesan meja restoran.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Recommendation cards side-by-side
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Buat Reservasi", icon=":material/calendar_add_on:", use_container_width=True):
            st.session_state.pending_prompt = "Saya ingin membuat reservasi meja"
            st.rerun()
    with col2:
        if st.button("Cek Status Reservasi", icon=":material/search:", use_container_width=True):
            st.session_state.pending_prompt = "Cek status reservasi saya"
            st.rerun()

        st.markdown("---")
        with st.form("form_cek_reservasi_id"):
            st.markdown("### Cek Reservasi dengan ID")
            reservation_id = st.text_input("Masukkan ID Reservasi", placeholder="RSV12345")
            if st.form_submit_button("Cari Reservasi"):
                query_result = find_reservation_by_id(reservation_id)
                if not reservation_id.strip():
                    st.warning("Mohon isi ID reservasi terlebih dahulu.")
                elif not query_result.get("found", False):
                    st.error("Reservasi tidak ditemukan. Pastikan ID benar.")
                else:
                    for reservation in query_result["reservations"]:
                        st.success("Reservasi ditemukan:")
                        st.markdown(render_reservation_detail(reservation))
                        st.markdown("---")
else:
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(message["content"])
