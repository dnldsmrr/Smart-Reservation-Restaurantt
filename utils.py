"""
utils.py – shared data loader and helpers with Railway MySQL
"""
import json
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import streamlit as st
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(os.path.dirname(__file__)) / '.env')

DATA_PATH = Path(os.path.dirname(__file__)) / "data.json"

# Railway MySQL Configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "thomas.proxy.rlwy.net")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "21018"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "FtdbLcDbRkOOjdxBVQdkbnKqPjrfsYtO")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "railway")
MYSQL_TABLE = os.getenv("MYSQL_TABLE", "reservations")


def _normalize_reservation_df(df: pd.DataFrame) -> pd.DataFrame:
    if "Tanggal Reservasi" not in df.columns and "Tanggal" in df.columns:
        df["Tanggal Reservasi"] = pd.to_datetime(df["Tanggal"], errors="coerce")
    elif "Tanggal Reservasi" in df.columns:
        df["Tanggal Reservasi"] = pd.to_datetime(df["Tanggal Reservasi"], errors="coerce")

    if "Tanggal" not in df.columns and "Tanggal Reservasi" in df.columns:
        df["Tanggal"] = df["Tanggal Reservasi"].dt.strftime("%Y-%m-%d")
    if "Bulan" not in df.columns and "Tanggal Reservasi" in df.columns:
        df["Bulan"] = df["Tanggal Reservasi"].dt.month
    if "Nama Bulan" not in df.columns and "Tanggal Reservasi" in df.columns:
        df["Nama Bulan"] = df["Tanggal Reservasi"].dt.strftime("%b")

    if "Rating" in df.columns:
        df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
    else:
        df["Rating"] = pd.Series([None] * len(df), dtype="float")

    if "Total Estimasi (IDR)" in df.columns:
        df["Total Estimasi (IDR)"] = pd.to_numeric(df["Total Estimasi (IDR)"], errors="coerce")
    else:
        df["Total Estimasi (IDR)"] = pd.Series([None] * len(df), dtype="float")

    return df


@st.cache_data
def load_local_data() -> pd.DataFrame:
    df = pd.read_json(DATA_PATH)
    return _normalize_reservation_df(df)


@st.cache_data
def load_mysql_data() -> Optional[pd.DataFrame]:
    conn = get_mysql_connection()
    if conn is None:
        return None

    try:
        query = f"SELECT * FROM {MYSQL_TABLE}"
        df = pd.read_sql(query, conn)
        conn.close()
        return _normalize_reservation_df(df)
    except Error as e:
        return None
    except Exception:
        return None


EXPECTED_MYSQL_COLUMNS = {
    "Reservation ID": "VARCHAR(50)",
    "Customer ID": "VARCHAR(50)",
    "Nama Customer": "VARCHAR(255)",
    "No. HP": "VARCHAR(50)",
    "Email": "VARCHAR(255)",
    "Tanggal Reservasi": "DATETIME",
    "Waktu Reservasi": "VARCHAR(20)",
    "Durasi (menit)": "INT",
    "Jumlah Orang": "INT",
    "Area Meja": "VARCHAR(100)",
    "Tipe Meja": "VARCHAR(100)",
    "Nomor Meja": "INT",
    "Occasion": "VARCHAR(100)",
    "Special Request": "TEXT",
    "Estimasi Budget/Orang (IDR)": "DOUBLE",
    "Total Estimasi (IDR)": "DOUBLE",
    "Metode Pembayaran": "VARCHAR(100)",
    "Channel Booking": "VARCHAR(100)",
    "Status Reservasi": "VARCHAR(50)",
    "Rating": "DOUBLE",
    "Catatan Staff": "TEXT",
    "Tanggal": "DATE",
    "Bulan": "INT"
}


def get_mysql_connection():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        return conn
    except Error as e:
        return None


def ensure_mysql_table() -> Tuple[bool, Optional[str]]:
    conn = get_mysql_connection()
    if conn is None:
        return False, "Koneksi MySQL tidak tersedia"

    try:
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS `{MYSQL_TABLE}` ("
            "id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY)"
        )
        cursor.execute(f"SHOW COLUMNS FROM `{MYSQL_TABLE}`")
        existing_columns = {row[0] for row in cursor.fetchall()}

        alter_clauses = []
        for column, sql_type in EXPECTED_MYSQL_COLUMNS.items():
            if column not in existing_columns:
                alter_clauses.append(f"ADD COLUMN `{column}` {sql_type} NULL")

        if alter_clauses:
            cursor.execute(f"ALTER TABLE `{MYSQL_TABLE}` {', '.join(alter_clauses)}")

        conn.commit()
        cursor.close()
        conn.close()
        return True, None
    except Error as e:
        return False, str(e)
    except Exception as exc:
        return False, str(exc)


def export_all_local_to_mysql() -> Tuple[bool, Optional[str]]:
    conn = get_mysql_connection()
    if conn is None:
        return False, "Koneksi MySQL tidak tersedia"

    df = load_local_data()
    if df.empty:
        return True, None

    try:
        cursor = conn.cursor()
        
        ensure_mysql_table()

        for _, row in df.iterrows():
            columns = ", ".join([f"`{col.replace('`', '``')}`" for col in row.index])
            placeholders = ", ".join(["%s"] * len(row))
            insert_query = f"INSERT INTO `{MYSQL_TABLE}` ({columns}) VALUES ({placeholders})"
            cursor.execute(insert_query, tuple(row))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, None
    except Error as e:
        return False, str(e)
    except Exception as exc:
        return False, str(exc)


def sync_reservation_to_mysql(record: dict) -> Tuple[bool, Optional[str]]:
    conn = get_mysql_connection()
    if conn is None:
        return False, "Koneksi MySQL tidak tersedia"

    try:
        cursor = conn.cursor()
        columns = ", ".join([f"`{col.replace('`', '``')}`" for col in record.keys()])
        placeholders = ", ".join(["%s"] * len(record))
        insert_query = f"INSERT INTO `{MYSQL_TABLE}` ({columns}) VALUES ({placeholders})"
        
        cursor.execute(insert_query, tuple(record.values()))
        conn.commit()
        cursor.close()
        conn.close()
        return True, None
    except Error as e:
        return False, str(e)
    except Exception as exc:
        return False, str(exc)


def load_data() -> pd.DataFrame:
    remote_df = load_mysql_data()
    if remote_df is None:
        return load_local_data()

    if remote_df.empty:
        local_df = load_local_data()
        if not local_df.empty:
            ensure_mysql_table()
            _export_ok, _ = export_all_local_to_mysql()
            remote_df = load_mysql_data()
            if remote_df is None:
                return local_df
        return remote_df

    return remote_df


def append_reservation(record: dict) -> dict:
    """Append a new reservation record to the JSON data store."""
    if not isinstance(record, dict):
        return {"success": False, "error": "Record must be a dict"}

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except Exception as exc:
        return {"success": False, "error": f"Gagal membaca data lokal: {exc}"}

    existing.append(record)

    try:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        return {"success": False, "error": f"Gagal menyimpan data lokal: {exc}"}

    for fn in (load_data, load_local_data, load_mysql_data):
        if hasattr(fn, "clear"):
            fn.clear()
        elif hasattr(fn, "clear_cache"):
            fn.clear_cache()

    synced, sync_error = sync_reservation_to_mysql(record)
    if synced:
        return {"success": True}
    return {"success": True, "warning": f"Reservasi disimpan lokal, tapi gagal sinkron ke MySQL: {sync_error}"}

MONTH_MAP = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"Mei",6:"Jun",
             7:"Jul",8:"Agu",9:"Sep",10:"Okt",11:"Nov",12:"Des"}

STATUS_COLORS = {
    "Confirmed":  "#28A745", # green
    "Completed":  "#007BFF", # blue
    "Pending":    "#FFA500", # orange
    "Cancelled":  "#DC3545", # red
    "No-show":    "#6C757D", # grey
    "confirmed":  "#28A745",
    "completed":  "#007BFF",
    "pending":    "#FFA500",
    "cancelled":  "#DC3545",
    "no_show":    "#6C757D"
}

GOLD  = "#FF6B35"  # Terracotta color mapping
DARK  = "#2D2522"  # Charcoal color mapping
CREAM = "#FFFBF8"  # Cream color mapping

COMMON_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20,500,0,0');

/* Hide Streamlit chrome — keep sidebar toggle for mobile */
#MainMenu { display: none !important; }
header[data-testid="stHeader"] { background-color: transparent !important; }
[data-testid="stToolbar"] { display: none !important; }
footer { display: none !important; }
.stDeployButton { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: flex !important; }
button[data-testid="collapsedControl"] { display: flex !important; }

html, body, [class*="css"] {
    font-family: 'Inter', 'Outfit', sans-serif !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E5E5E5 !important;
}

.main .block-container {
    background: #F4F4F4 !important;
    padding: 86px 2.5rem 2rem !important;
}

/* ── Fixed full-width top nav bar (shared by all pages) ── */
.sara-nav-bar {
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
}
.sara-nav-chip {
    background: #FFFBF8;
    color: #FF6B35;
    border: 1px solid #FFE0D3;
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    white-space: nowrap;
}

/* Full width when sidebar is collapsed */
.stMainBlockContainer {
    max-width: 100% !important;
}

/* Consistent orange-gradient buttons across all admin pages */
.stButton > button,
[data-testid="stFormSubmitButton"] > button {
    border-radius: 999px !important;
    border: none !important;
    background: linear-gradient(135deg, #FF6B35, #FF8E66) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    box-shadow: 0 6px 20px rgba(255,107,53,0.15) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.stButton > button:hover:not(:disabled),
[data-testid="stFormSubmitButton"] > button:hover:not(:disabled) {
    transform: translateY(-1px) !important;
    box-shadow: 0 10px 28px rgba(255,107,53,0.2) !important;
}
.stButton > button:disabled,
[data-testid="stFormSubmitButton"] > button:disabled {
    background: #e2e2e2 !important;
    color: #7a7a7a !important;
    box-shadow: none !important;
}

/* KPI Card */
.kpi-card {
    background: white;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    border-left: 4px solid var(--accent,#FF6B35);
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    margin-bottom: 1rem;
}
.kpi-label {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #888;
    font-weight: 600;
    margin-bottom: 4px;
}
.kpi-value {
    font-family: 'Outfit', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #2D2522;
    line-height: 1.1;
}
.kpi-sub {
    font-size: 0.8rem;
    color: #aaa;
    margin-top: 4px;
}

/* Section title */
.section-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.35rem;
    font-weight: 700;
    color: #2D2522;
    margin: 2rem 0 1rem;
    display: flex;
    align-items: center;
    gap: 10px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(to right, #FF6B35, transparent);
}

/* Badge */
.badge {
    display: inline-block;
    border-radius: 50px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 600;
}
.back-button-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 1.5rem;
}
.back-button {
    display: inline-flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.95rem 1.4rem;
    border-radius: 999px;
    background: linear-gradient(135deg, #FF6B35, #FF8E66);
    color: #FFFFFF;
    text-decoration: none;
    font-weight: 700;
    box-shadow: 0 14px 32px rgba(255, 107, 53, 0.18);
    transition: transform .18s ease, box-shadow .18s ease, opacity .18s ease;
}
.back-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 18px 38px rgba(255, 107, 53, 0.22);
    opacity: 0.98;
    color: #FFFFFF !important;
}
.back-button-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.2rem;
    height: 2.2rem;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.2);
    color: #FFFFFF;
    font-size: 1.05rem;
}

/* ── Floating "Show Menu" FAB when sidebar is collapsed ── */
div.element-container:has(#sara-show-menu-marker) + div.element-container .stButton > button {
    position: fixed !important;
    top: 12px !important;
    left: 12px !important;
    z-index: 99999 !important;
    width: 46px !important;
    height: 46px !important;
    min-height: 46px !important;
    border-radius: 12px !important;
    padding: 0 !important;
    background: linear-gradient(135deg, #FF6B35, #FF8E66) !important;
    box-shadow: 0 4px 14px rgba(255,107,53,0.4) !important;
    border: none !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
}
div.element-container:has(#sara-show-menu-marker) + div.element-container .stButton > button:hover {
    transform: scale(1.08) !important;
    box-shadow: 0 6px 18px rgba(255,107,53,0.5) !important;
}
div.element-container:has(#sara-show-menu-marker) + div.element-container .stButton > button *,
div.element-container:has(#sara-show-menu-marker) + div.element-container .stButton > button svg,
div.element-container:has(#sara-show-menu-marker) + div.element-container .stButton > button svg path {
    fill: white !important;
    color: white !important;
}
/* Prevent the FAB element container from occupying layout space */
div.element-container:has(#sara-show-menu-marker),
div.element-container:has(#sara-show-menu-marker) + div.element-container:has(.stButton) {
    height: 0 !important;
    overflow: visible !important;
    margin: 0 !important;
    padding: 0 !important;
}
</style>
"""

def load_css(css_file_name: str):
    """Load a CSS file from the styles/ directory and inject it into the Streamlit app."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(current_dir, "styles", css_file_name)
    
    if os.path.exists(css_path):
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error loading CSS: {e}")
    else:
        st.warning(f"CSS stylesheet not found: {css_file_name}")

def check_admin_login():
    """Redirect to Beranda if admin session is not active."""
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
    if "admin_sidebar_open" not in st.session_state:
        st.session_state.admin_sidebar_open = True
    if not st.session_state.admin_logged_in:
        st.switch_page("Beranda.py")
        st.stop()