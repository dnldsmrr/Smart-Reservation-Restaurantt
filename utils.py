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
    "Confirmed":  "#2ecc71",
    "Completed":  "#3498db",
    "Pending":    "#f39c12",
    "Cancelled":  "#e74c3c",
    "No-show":    "#9b59b6",
}

GOLD  = "#d4af37"
DARK  = "#0f1923"
CREAM = "#e8dcc8"

COMMON_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
section[data-testid="stSidebar"] {
    background: linear-gradient(160deg,#0f1923 0%,#1a2a3a 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.07);
}
section[data-testid="stSidebar"] * { color: #e8dcc8 !important; }
.main .block-container { background:#f7f3ee; padding:2rem 2.5rem; }

/* KPI Card */
.kpi-card {
    background: white;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    border-left: 4px solid var(--accent,#d4af37);
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    margin-bottom: 1rem;
}
.kpi-label { font-size:0.78rem; text-transform:uppercase; letter-spacing:1px;
             color:#888; font-weight:600; margin-bottom:4px; }
.kpi-value { font-family:'Playfair Display',serif; font-size:2rem;
             font-weight:700; color:#0f1923; line-height:1.1; }
.kpi-sub   { font-size:0.8rem; color:#aaa; margin-top:4px; }

/* Section title */
.section-title {
    font-family:'Playfair Display',serif;
    font-size:1.35rem; font-weight:700;
    color:#0f1923; margin:2rem 0 1rem;
    display:flex; align-items:center; gap:10px;
}
.section-title::after {
    content:''; flex:1; height:1px;
    background:linear-gradient(to right,#d4af37,transparent);
}

/* Badge */
.badge {
    display:inline-block; border-radius:50px;
    padding:3px 12px; font-size:0.78rem; font-weight:600;
}
.back-button-wrapper {
    display:flex; justify-content:center; margin-top:1.5rem;
}
.back-button {
    display:inline-flex; align-items:center; gap:0.75rem;
    padding:0.95rem 1.4rem; border-radius:999px;
    background: linear-gradient(135deg,#d4af37,#f7e6a4);
    color:#0f1923; text-decoration:none; font-weight:700;
    box-shadow:0 14px 32px rgba(212,175,55,0.18);
    transition:transform .18s ease, box-shadow .18s ease, opacity .18s ease;
}
.back-button:hover {
    transform:translateY(-2px);
    box-shadow:0 18px 38px rgba(212,175,55,0.22);
    opacity:0.98;
}
.back-button-icon {
    display:inline-flex; align-items:center; justify-content:center;
    width:2.2rem; height:2.2rem; border-radius:50%;
    background:rgba(15,25,35,0.08); color:#0f1923;
    font-size:1.05rem;
}
</style>
"""