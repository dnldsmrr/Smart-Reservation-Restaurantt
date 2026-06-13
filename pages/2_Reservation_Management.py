import streamlit as st
import pandas as pd
import sys, os, base64
from datetime import date
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_mysql_data, load_local_data, COMMON_CSS, STATUS_COLORS, GOLD, DARK, CREAM, check_admin_login

# ── Logo helper ──
def _get_b64(path):
    try:
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return ""

_logo_b64 = _get_b64(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "sara_logo.png"))
_LOGO = (f'<img src="data:image/png;base64,{_logo_b64}" style="width:44px;height:44px;border-radius:10px;box-shadow:0 2px 5px rgba(0,0,0,0.06);object-fit:cover;">'
         if _logo_b64 else '<div style="width:44px;height:44px;background:#EAEAEA;border-radius:10px;"></div>')

# Initialize session state BEFORE set_page_config
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "admin_sidebar_open" not in st.session_state:
    st.session_state.admin_sidebar_open = True

_sidebar_state = "expanded" if st.session_state.admin_sidebar_open else "collapsed"
st.set_page_config(page_title="Manajemen Reservasi · Smart Reservation",
                   page_icon=":material/table_chart:", layout="wide",
                   initial_sidebar_state=_sidebar_state)
st.markdown(COMMON_CSS, unsafe_allow_html=True)
st.markdown(f"""<style>
.sara-nav-bar{{position:fixed;top:0;left:0;right:0;height:72px;z-index:999998;
    background:#FFFFFF;border-bottom:1px solid #EAEAEA;padding:0 2rem;
    box-sizing:border-box;display:flex;align-items:center;
    justify-content:space-between;box-shadow:0 1px 6px rgba(0,0,0,0.04);}}
.sara-nav-chip{{background:{CREAM};color:{GOLD};border:1px solid #FFE0D3;
    border-radius:20px;padding:6px 14px;font-size:12px;font-weight:600;
    font-family:'Inter',sans-serif;white-space:nowrap;}}
</style>""", unsafe_allow_html=True)

# ✅ Authentication Check
check_admin_login()

# ── Top nav bar ──
st.markdown(f"""
<div class="sara-nav-bar">
    <div style="display:flex;align-items:center;gap:14px;">
        {_LOGO}
        <div>
            <div style="font-weight:800;font-size:18px;color:{DARK};
                 font-family:'Outfit',sans-serif;letter-spacing:-0.3px;line-height:1.1;">
                Sara Nusantara
            </div>
            <div style="font-size:11px;color:#8E8E8E;margin-top:3px;
                 display:flex;align-items:center;gap:5px;">
                <span style="color:{GOLD};font-size:9px;">●</span>
                Admin Panel · Mandala Rasa
            </div>
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:10px;">
        <span class="sara-nav-chip">Admin Panel</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Floating "Show Menu" FAB — only rendered when sidebar is collapsed
if not st.session_state.admin_sidebar_open:
    st.markdown("""<style>
div.element-container:has(#sara-show-menu-marker)+div.element-container .stButton>button{
    position:fixed!important;top:14px!important;left:14px!important;
    z-index:9999990!important;width:46px!important;height:46px!important;
    min-height:46px!important;border-radius:12px!important;padding:0!important;
    background:linear-gradient(135deg,#FF6B35,#FF8E66)!important;
    box-shadow:0 4px 14px rgba(255,107,53,0.4)!important;border:none!important;
    transition:transform 0.18s ease,box-shadow 0.18s ease!important;
}
div.element-container:has(#sara-show-menu-marker)+div.element-container .stButton>button:hover{
    transform:scale(1.08)!important;box-shadow:0 6px 18px rgba(255,107,53,0.5)!important;
}
div.element-container:has(#sara-show-menu-marker)+div.element-container .stButton>button svg,
div.element-container:has(#sara-show-menu-marker)+div.element-container .stButton>button svg path,
div.element-container:has(#sara-show-menu-marker)+div.element-container .stButton>button span{
    fill:white!important;color:white!important;
}
div.element-container:has(#sara-show-menu-marker),
div.element-container:has(#sara-show-menu-marker)+div.element-container:has(.stButton){
    height:0!important;overflow:visible!important;margin:0!important;padding:0!important;
}
</style><span id="sara-show-menu-marker" style="display:none;"></span>""", unsafe_allow_html=True)
    if st.button("", icon=":material/menu:", key="show_sidebar_btn"):
        st.session_state.admin_sidebar_open = True
        st.rerun()

st.markdown("""
<style>
.main .block-container { background:#F4F4F4 !important; padding:86px 2.2rem 1.8rem !important; }

/* ── Header ── */
.page-header {
    background: linear-gradient(135deg,#FF6B35 0%,#FF8E66 100%);
    border-radius:18px; padding:28px 36px; color:#FFFFFF;
    display:flex; justify-content:space-between; align-items:center;
    margin-bottom:1.4rem;
    box-shadow: 0 8px 32px rgba(255, 107, 53, 0.18);
}
.page-header .badge { font-size:0.7rem; letter-spacing:2.5px; text-transform:uppercase;
    color:#FFFBF8; font-weight:700; margin-bottom:6px; display:block; }
.page-header h1 { font-family:'Outfit',sans-serif; font-size:1.9rem;
    margin:0 0 4px; color:#FFFFFF; }
.page-header p  { margin:0; color:rgba(255,255,255,0.85); font-size:0.88rem; }
.page-header-icon { width:64px; height:64px; border-radius:50%;
    background:rgba(255,255,255,0.15); border:1.5px solid rgba(255,255,255,0.35);
    display:flex; align-items:center; justify-content:center; font-size:1.8rem; color:#FFFFFF; }

/* ── Filter card ── */
.filter-card {
    background:white; border-radius:14px; padding:1.4rem 1.8rem;
    box-shadow:0 2px 14px rgba(0,0,0,0.06); margin-bottom:1.2rem;
    border-top:3px solid #FF6B35;
}

/* ── Table ── */
.tbl-wrap { border-radius:14px; overflow:hidden;
    box-shadow:0 2px 14px rgba(0,0,0,0.07); margin-bottom:1.2rem; }
.tbl-header {
    background:linear-gradient(135deg,#2D2522,#403531); color:#FFFBF8;
    padding:13px 18px; font-weight:600; font-size:0.82rem; letter-spacing:0.3px;
    display:grid; grid-template-columns:140px 1fr 110px 70px 130px 120px; gap:10px;
}
.tbl-row {
    background:white; border-bottom:1px solid #f0ebe3;
    padding:13px 18px; font-size:0.86rem; color:#333;
    display:grid; grid-template-columns:140px 1fr 110px 70px 130px 120px;
    gap:10px; align-items:center; transition:background .15s;
}
.tbl-row:hover { background:#FFF9F6; }
.tbl-row:last-child { border-bottom:none; }
.rsv-id-text { font-weight:700; color:#FF6B35; font-size:0.8rem; }

/* ── Detail card ── */
.detail-card {
    background:white; border-radius:16px; padding:1.8rem 2.2rem;
    box-shadow:0 4px 24px rgba(0,0,0,0.08); border-left:5px solid #FF6B35;
}
.detail-name { font-family:'Outfit',sans-serif; font-size:1.5rem;
    font-weight:700; color:#2D2522; margin:6px 0; }
.detail-id   { font-size:0.78rem; color:#aaa; font-weight:600; letter-spacing:1px; }
.detail-contact { display:flex; gap:20px; flex-wrap:wrap;
    font-size:0.87rem; color:#555; margin-bottom:1rem; }
.detail-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:1rem; }
.detail-item { background:#FFF9F6; border-radius:10px; padding:11px 14px; }
.detail-lbl  { font-size:0.7rem; text-transform:uppercase; letter-spacing:0.8px;
    color:#999; margin-bottom:3px; font-weight:600; }
.detail-val  { font-size:0.93rem; font-weight:600; color:#2D2522; }
.status-pill { display:inline-block; border-radius:50px; padding:4px 14px;
    font-size:0.76rem; font-weight:700; color:white; margin-left:10px; }
.note-box { background:#fff8e1; border-radius:9px; padding:10px 14px;
    font-size:0.84rem; color:#795800; margin-top:12px;
    border-left:3px solid #f39c12; }
.revenue-val { color:#FF6B35 !important; font-size:1.1rem !important;
    font-weight:700 !important; }

/* ── Pagination ── */
.stNumberInput { max-width:120px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.markdown("<h3 style='margin-top:0; padding-top:0; color:#FF6B35;'>SARA Admin</h3>", unsafe_allow_html=True)
    st.write("Sistem manajemen reservasi Mandala Rasa.")
    st.markdown("---")
    
    st.page_link("Beranda.py", label="Halaman Chat Utama", icon=":material/chat:")
    st.page_link("pages/1_Dashboard_Analytics.py", label="Dashboard Analytics", icon=":material/bar_chart:")
    st.page_link("pages/2_Reservation_Management.py", label="Kelola Reservasi", icon=":material/table_chart:")

    st.markdown("---")
    if st.button("Keluar Admin", icon=":material/logout:", use_container_width=True, key="reservations_logout"):
        st.session_state.admin_logged_in = False
        st.toast("Admin keluar.")
        st.rerun()


# ── Load data ──
df_all = load_mysql_data()
if df_all is None or df_all.empty:
    st.warning("MySQL tidak tersedia atau kosong, menggunakan data lokal sebagai fallback.")
    df_all = load_local_data()

# Pastikan kolom Tanggal Reservasi bertipe datetime
if "Tanggal Reservasi" in df_all.columns:
    if not pd.api.types.is_datetime64_any_dtype(df_all["Tanggal Reservasi"]):
        df_all["Tanggal Reservasi"] = pd.to_datetime(df_all["Tanggal Reservasi"], errors="coerce")
elif "Tanggal" in df_all.columns:
    df_all["Tanggal Reservasi"] = pd.to_datetime(df_all["Tanggal"], errors="coerce")
else:
    df_all["Tanggal Reservasi"] = pd.NaT

# ── Header ──
st.markdown("""
<div class="page-header">
  <div>
    <span class="badge">✦ Admin · Restaurant</span>
    <h1>Manajemen Reservasi</h1>
    <p>Cari, filter, lihat detail, dan ekspor data reservasi</p>
  </div>
  <div class="page-header-icon"><span class="material-symbols-outlined" style="font-size:1.8rem;font-variation-settings:'FILL' 1,'wght' 400,'GRAD' 0,'opsz' 48;">table_chart</span></div>
</div>
""", unsafe_allow_html=True)

# ══════════════ FILTER ══════════════
st.markdown('<div class="section-title"><span class="material-symbols-outlined" style="vertical-align:middle;font-size:1.2rem;margin-right:6px;">search</span>Pencarian & Filter</div>', unsafe_allow_html=True)

with st.container():
    f1, f2, f3, f4, f5 = st.columns([2.2, 1.4, 1.4, 1.4, 1.4])
    with f1:
        search = st.text_input("Cari nama / ID Reservasi / ID Customer",
                               placeholder="Contoh: Andi, RSV00001, CUST001 ...")
    with f2:
        status_opts = ["Semua"] + sorted(df_all["Status Reservasi"].dropna().unique().tolist())
        status_sel  = st.selectbox("Status", status_opts)
    with f3:
        area_opts = ["Semua"] + sorted(df_all["Area Meja"].dropna().unique().tolist())
        area_sel  = st.selectbox("Area Meja", area_opts)
    with f4:
        ch_opts = ["Semua"] + sorted(df_all["Channel Booking"].dropna().unique().tolist())
        ch_sel  = st.selectbox("Channel", ch_opts)
    with f5:
        occ_opts = ["Semua"] + sorted(df_all["Occasion"].dropna().unique().tolist())
        occ_sel  = st.selectbox("Occasion", occ_opts)

    d1, d2 = st.columns(2)
    with d1:
        min_date = df_all["Tanggal Reservasi"].min().date() if not df_all["Tanggal Reservasi"].isna().all() else date.today()
        max_date = df_all["Tanggal Reservasi"].max().date() if not df_all["Tanggal Reservasi"].isna().all() else date.today()
        date_from = st.date_input("Dari Tanggal", value=min_date,
                                  min_value=min_date, max_value=max_date)
    with d2:
        date_to = st.date_input("Sampai Tanggal", value=max_date,
                                min_value=min_date, max_value=max_date)

    if date_from > date_to:
        date_from, date_to = date_to, date_from

# ── Apply filters ──
df = df_all.copy()

if search and search.strip():
    q = search.strip()
    mask = (
        df["Nama Customer"].astype(str).str.contains(q, case=False, na=False) |
        df["Reservation ID"].astype(str).str.contains(q, case=False, na=False) |
        df["Customer ID"].astype(str).str.contains(q, case=False, na=False)
    )
    df = df[mask]

if status_sel != "Semua": df = df[df["Status Reservasi"] == status_sel]
if area_sel   != "Semua": df = df[df["Area Meja"]        == area_sel]
if ch_sel     != "Semua": df = df[df["Channel Booking"]  == ch_sel]
if occ_sel    != "Semua": df = df[df["Occasion"]         == occ_sel]

df = df[
    (df["Tanggal Reservasi"].dt.date >= date_from) &
    (df["Tanggal Reservasi"].dt.date <= date_to)
]
df = df.reset_index(drop=True)

# ── Summary bar + Download ──
sc1, sc2 = st.columns([3, 1])
with sc1:
    total_rev_filt = df["Total Estimasi (IDR)"].sum()
    avg_pax = df["Jumlah Orang"].mean() if len(df) > 0 else 0
    st.markdown(
        f"Menampilkan **{len(df):,}** reservasi &nbsp;·&nbsp; "
        f"Total Revenue: **Rp {total_rev_filt/1_000_000:.1f} Jt** &nbsp;·&nbsp; "
        f"Avg Party Size: **{avg_pax:.1f} orang**"
    )
with sc2:
    csv_cols = ["Reservation ID","Customer ID","Nama Customer","No. HP","Email",
                "Tanggal","Waktu Reservasi","Jumlah Orang","Area Meja","Tipe Meja",
                "Occasion","Special Request","Total Estimasi (IDR)","Metode Pembayaran",
                "Channel Booking","Status Reservasi","Rating","Catatan Staff"]
    # Hanya ambil kolom yang ada
    csv_cols = [c for c in csv_cols if c in df.columns]
    csv_data = df[csv_cols].to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", data=csv_data,
                       file_name="reservasi_export.csv",
                       mime="text/csv", use_container_width=True)

# ══════════════ TABLE ══════════════
st.markdown('<div class="section-title"><span class="material-symbols-outlined" style="vertical-align:middle;font-size:1.2rem;margin-right:6px;">list_alt</span>Daftar Reservasi</div>', unsafe_allow_html=True)

if df.empty:
    st.info("Tidak ada data yang cocok dengan filter yang dipilih.")
else:
    PAGE_SIZE   = 15
    total_pages = max(1, (len(df) - 1) // PAGE_SIZE + 1)
    if "reservation_page" not in st.session_state:
        st.session_state.reservation_page = 1
    if st.session_state.reservation_page > total_pages:
        st.session_state.reservation_page = total_pages

    page_row_left, page_row_center, page_row_right = st.columns([1, 1, 1])
    with page_row_left:
        prev_clicked = st.button("← Previous", use_container_width=True,
                                 disabled=(st.session_state.reservation_page <= 1), key="prev_page")
    with page_row_center:
        st.markdown(f"<div style='padding:12px 0; text-align:center; color:#333; font-size:0.95rem; line-height:1.2;'>"
                    f"<strong>{st.session_state.reservation_page}</strong> / <strong>{total_pages}</strong><br>"
                    f"{len(df):,} data</div>", unsafe_allow_html=True)
    with page_row_right:
        next_clicked = st.button("Next →", use_container_width=True,
                                 disabled=(st.session_state.reservation_page >= total_pages), key="next_page")

    if prev_clicked:
        st.session_state.reservation_page = max(1, st.session_state.reservation_page - 1)
        st.rerun()
    if next_clicked:
        st.session_state.reservation_page = min(total_pages, st.session_state.reservation_page + 1)
        st.rerun()

    page_df = df.iloc[(st.session_state.reservation_page-1)*PAGE_SIZE : st.session_state.reservation_page*PAGE_SIZE]

    # Table header + rows
    st.markdown("""
    <div class="tbl-wrap">
      <div class="tbl-header">
        <span>ID Reservasi</span>
        <span>Nama Customer</span>
        <span>Tanggal</span>
        <span>Pax</span>
        <span>Area Meja</span>
        <span>Status</span>
      </div>""", unsafe_allow_html=True)

    rows_html = ""
    for _, row in page_df.iterrows():
        sc    = STATUS_COLORS.get(str(row.get("Status Reservasi","")), "#ccc")
        nama  = str(row.get("Nama Customer","—"))
        tgl   = str(row.get("Tanggal","—"))
        rsv   = str(row.get("Reservation ID","—"))
        area  = str(row.get("Area Meja","—"))
        stat  = str(row.get("Status Reservasi","—"))
        pax_v = row.get("Jumlah Orang", 0)
        pax   = int(pax_v) if pd.notna(pax_v) else "-"
        rows_html += f"""
      <div class="tbl-row">
        <span class="rsv-id-text">{rsv}</span>
        <span style="font-weight:600">{nama}</span>
        <span style="color:#666">{tgl}</span>
        <span><span class="material-symbols-outlined" style="font-size:0.9rem;vertical-align:middle;">group</span> {pax}</span>
        <span>{area}</span>
        <span><span style="background:{sc};color:white;border-radius:50px;
              padding:3px 10px;font-size:0.73rem;font-weight:700">{stat}</span></span>
      </div>"""
    st.markdown(rows_html + "</div>", unsafe_allow_html=True)

    # ══════════════ DETAIL VIEW ══════════════
    st.markdown('<div class="section-title"><span class="material-symbols-outlined" style="vertical-align:middle;font-size:1.2rem;margin-right:6px;">info</span>Detail Reservasi</div>', unsafe_allow_html=True)

    id_list = page_df["Reservation ID"].tolist()
    selected_id = st.selectbox("Pilih ID Reservasi:", id_list,
                               format_func=lambda x: f"{x}")

    if selected_id:
        rows_found = df[df["Reservation ID"] == selected_id]
        if not rows_found.empty:
            row = rows_found.iloc[0]
            sc  = STATUS_COLORS.get(str(row.get("Status Reservasi","")), "#aaa")

            # Safe getters
            def sv(col, default="—"):
                v = row.get(col, default)
                return default if pd.isna(v) or str(v) in ("nan","None","") else str(v)

            def iv(col, default=0):
                v = row.get(col, default)
                try: return int(float(v)) if pd.notna(v) else default
                except: return default

            rating_str  = f'<span class="material-symbols-outlined" style="font-size:0.9rem;vertical-align:middle;font-variation-settings:\'FILL\' 1,\'wght\' 400,\'GRAD\' 0,\'opsz\' 24;color:#FFA500;">star</span> {float(sv("Rating","")):.1f}' if sv("Rating") not in ["—","nan"] else "Belum ada rating"
            revenue_raw = row.get("Total Estimasi (IDR)", 0)
            revenue_str = f"Rp {int(float(revenue_raw)):,}" if pd.notna(revenue_raw) else "—"
            catatan     = sv("Catatan Staff")
            special_req = sv("Special Request")
            if special_req in ["None","Tidak ada",""]: special_req = "Tidak ada"

            st.markdown(f"""
            <div class="detail-card">
              <div class="detail-id">{sv('Reservation ID')} &nbsp;·&nbsp; {sv('Customer ID')}</div>
              <div class="detail-name">
                {sv('Nama Customer')}
                <span class="status-pill" style="background:{sc}">{sv('Status Reservasi')}</span>
              </div>
              <div class="detail-contact">
                <span><span class="material-symbols-outlined" style="font-size:0.9rem;vertical-align:middle;">call</span> {sv('No. HP')}</span>
                <span><span class="material-symbols-outlined" style="font-size:0.9rem;vertical-align:middle;">mail</span> {sv('Email')}</span>
                <span><span class="material-symbols-outlined" style="font-size:0.9rem;vertical-align:middle;">calendar_today</span> {sv('Tanggal')} · {sv('Waktu Reservasi')}</span>
                <span><span class="material-symbols-outlined" style="font-size:0.9rem;vertical-align:middle;">smartphone</span> {sv('Channel Booking')}</span>
              </div>
              <div class="detail-grid">
                <div class="detail-item">
                  <div class="detail-lbl">Area & Meja</div>
                  <div class="detail-val"><span class="material-symbols-outlined" style="font-size:0.9rem;vertical-align:middle;">chair</span> {sv('Area Meja')} · {sv('Tipe Meja')} (No. {iv('Nomor Meja')})</div>
                </div>
                <div class="detail-item">
                  <div class="detail-lbl">Jumlah Tamu & Durasi</div>
                  <div class="detail-val"><span class="material-symbols-outlined" style="font-size:0.9rem;vertical-align:middle;">group</span> {iv('Jumlah Orang')} orang · <span class="material-symbols-outlined" style="font-size:0.9rem;vertical-align:middle;">timer</span> {iv('Durasi (menit)')} menit</div>
                </div>
                <div class="detail-item">
                  <div class="detail-lbl">Occasion</div>
                  <div class="detail-val"><span class="material-symbols-outlined" style="font-size:0.9rem;vertical-align:middle;">celebration</span> {sv('Occasion')}</div>
                </div>
                <div class="detail-item">
                  <div class="detail-lbl">Special Request</div>
                  <div class="detail-val"><span class="material-symbols-outlined" style="font-size:0.9rem;vertical-align:middle;">edit_note</span> {special_req}</div>
                </div>
                <div class="detail-item">
                  <div class="detail-lbl">Metode Pembayaran</div>
                  <div class="detail-val"><span class="material-symbols-outlined" style="font-size:0.9rem;vertical-align:middle;">credit_card</span> {sv('Metode Pembayaran')}</div>
                </div>
                <div class="detail-item">
                  <div class="detail-lbl">Rating Customer</div>
                  <div class="detail-val">{rating_str}</div>
                </div>
                <div class="detail-item" style="grid-column:span 2">
                  <div class="detail-lbl">Total Estimasi Revenue</div>
                  <div class="detail-val revenue-val">{revenue_str}</div>
                </div>
              </div>
              {"" if catatan == "—" else f'<div class="note-box"><span class="material-symbols-outlined" style="font-size:0.9rem;vertical-align:middle;">push_pin</span> <b>Catatan Staff:</b> {catatan}</div>'}
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")
st.caption("Smart Reservation System · Manajemen Reservasi · Kelompok 3 Hana Jatmiana")
