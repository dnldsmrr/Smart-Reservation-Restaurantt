"""
utils.py – shared data loader and helpers with Railway MySQL
"""
import json
import re
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
MYSQL_CUSTOMERS_TABLE = os.getenv("MYSQL_CUSTOMERS_TABLE", "customers")
MYSQL_TABLES_TABLE = os.getenv("MYSQL_TABLES_TABLE", "tables")
MYSQL_RESERVATIONS_TABLE = MYSQL_TABLE
MYSQL_PAYMENTS_TABLE = os.getenv("MYSQL_PAYMENTS_TABLE", "payments")
MYSQL_REVIEWS_TABLE = os.getenv("MYSQL_REVIEWS_TABLE", "reviews")

# Internal flag to avoid repeating expensive schema migration queries
_SCHEMA_ENSURED = False


def _parse_capacity_from_tipe(tipe_meja: Optional[str], jumlah_orang: Optional[int]) -> Optional[int]:
    if isinstance(tipe_meja, str):
        digits = re.findall(r"(\d+)", tipe_meja)
        if digits:
            return int(digits[0])
    if jumlah_orang is not None:
        try:
            return int(jumlah_orang)
        except Exception:
            pass
    return None


def _normalize_reservation_df(df: pd.DataFrame) -> pd.DataFrame:
    if "Tanggal Reservasi" not in df.columns and "Tanggal" in df.columns:
        df["Tanggal Reservasi"] = pd.to_datetime(df["Tanggal"], errors="coerce")
    elif "Tanggal Reservasi" in df.columns:
        df["Tanggal Reservasi"] = pd.to_datetime(df["Tanggal Reservasi"], errors="coerce")

    if "Tanggal" not in df.columns and "Tanggal Reservasi" in df.columns:
        df["Tanggal"] = df["Tanggal Reservasi"].dt.strftime("%Y-%m-%d")
    if "Waktu Reservasi" not in df.columns and "Tanggal Reservasi" in df.columns:
        df["Waktu Reservasi"] = df["Tanggal Reservasi"].dt.strftime("%H:%M")
    if "Bulan" not in df.columns and "Tanggal Reservasi" in df.columns:
        df["Bulan"] = df["Tanggal Reservasi"].dt.month
    if "Nama Bulan" not in df.columns and "Tanggal Reservasi" in df.columns:
        df["Nama Bulan"] = df["Tanggal Reservasi"].dt.strftime("%b")

    if "Nomor Meja" not in df.columns and "table_id" in df.columns:
        df["Nomor Meja"] = df["table_id"]

    if "Tipe Meja" not in df.columns and "kapasitas" in df.columns:
        df["Tipe Meja"] = df["kapasitas"].apply(lambda v: f"Meja {int(v)} Orang" if pd.notna(v) else None)

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
        query = f"""
            SELECT
                r.reservation_id AS `Reservation ID`,
                c.customer_id AS `Customer ID`,
                c.nama_customer AS `Nama Customer`,
                c.phone AS `No. HP`,
                c.email AS `Email`,
                r.tanggal_reservasi AS `Tanggal Reservasi`,
                r.durasi_menit AS `Durasi (menit)`,
                r.jumlah_orang AS `Jumlah Orang`,
                t.area_meja AS `Area Meja`,
                t.tipe_meja AS `Tipe Meja`,
                t.table_id AS `Nomor Meja`,
                r.occasion AS `Occasion`,
                r.special_request AS `Special Request`,
                p.metode_pembayaran AS `Metode Pembayaran`,
                p.budget_per_orang AS `Estimasi Budget/Orang (IDR)`,
                p.total_estimasi AS `Total Estimasi (IDR)`,
                r.channel_booking AS `Channel Booking`,
                r.status_reservasi AS `Status Reservasi`,
                rev.rating AS `Rating`,
                rev.catatan_staff AS `Catatan Staff`
            FROM `{MYSQL_RESERVATIONS_TABLE}` r
            LEFT JOIN `{MYSQL_CUSTOMERS_TABLE}` c ON c.customer_id COLLATE utf8mb4_unicode_ci = r.customer_id COLLATE utf8mb4_unicode_ci
            LEFT JOIN `{MYSQL_TABLES_TABLE}` t ON t.table_id = r.table_id
            LEFT JOIN `{MYSQL_PAYMENTS_TABLE}` p ON p.reservation_id COLLATE utf8mb4_unicode_ci = r.reservation_id COLLATE utf8mb4_unicode_ci
            LEFT JOIN `{MYSQL_REVIEWS_TABLE}` rev ON rev.reservation_id COLLATE utf8mb4_unicode_ci = r.reservation_id COLLATE utf8mb4_unicode_ci
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        df = pd.DataFrame(rows)
        return _normalize_reservation_df(df)
    except Exception:
        return None


def _ensure_column(cursor, table: str, column_name: str, definition: str):
    cursor.execute(f"SHOW COLUMNS FROM `{table}` LIKE %s", (column_name,))
    if cursor.fetchone() is None:
        cursor.execute(f"ALTER TABLE `{table}` ADD COLUMN {definition}")


def _rename_column_if_exists(cursor, table: str, old_name: str, new_name: str, definition: str):
    cursor.execute(f"SHOW COLUMNS FROM `{table}` LIKE %s", (old_name,))
    if cursor.fetchone() is not None:
        cursor.execute(f"ALTER TABLE `{table}` CHANGE COLUMN `{old_name}` `{new_name}` {definition}")


def _ensure_nullable_column(cursor, table: str, column_name: str, definition: str):
    cursor.execute(f"SHOW COLUMNS FROM `{table}` LIKE %s", (column_name,))
    row = cursor.fetchone()
    if row is None:
        cursor.execute(f"ALTER TABLE `{table}` ADD COLUMN {definition}")
    else:
        nullability = row[2].upper() if len(row) > 2 and row[2] is not None else "YES"
        if nullability == "NO":
            cursor.execute(f"ALTER TABLE `{table}` MODIFY COLUMN `{column_name}` {definition}")


def ensure_mysql_schema() -> Tuple[bool, Optional[str]]:
    conn = get_mysql_connection()
    if conn is None:
        return False, "Koneksi MySQL tidak tersedia"

    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS `{MYSQL_CUSTOMERS_TABLE}` (
            customer_id VARCHAR(50) NOT NULL PRIMARY KEY,
            nama_customer VARCHAR(255) NULL,
            phone VARCHAR(50) NULL,
            email VARCHAR(255) NULL)"""
        )
        cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS `{MYSQL_TABLES_TABLE}` (
            table_id INT NOT NULL PRIMARY KEY,
            area_meja VARCHAR(100) NULL,
            tipe_meja VARCHAR(100) NULL,
            kapasitas INT NULL)"""
        )
        cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS `{MYSQL_RESERVATIONS_TABLE}` (
            reservation_id VARCHAR(50) NOT NULL PRIMARY KEY,
            customer_id VARCHAR(50) NULL,
            table_id INT NULL,
            tanggal_reservasi DATETIME NULL,
            durasi_menit INT NULL,
            jumlah_orang INT NULL,
            occasion VARCHAR(100) NULL,
            special_request TEXT NULL,
            status_reservasi VARCHAR(50) NULL,
            channel_booking VARCHAR(100) NULL,
            FOREIGN KEY (customer_id) REFERENCES `{MYSQL_CUSTOMERS_TABLE}`(customer_id),
            FOREIGN KEY (table_id) REFERENCES `{MYSQL_TABLES_TABLE}`(table_id))"""
        )
        cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS `{MYSQL_PAYMENTS_TABLE}` (
            payment_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            reservation_id VARCHAR(50) NULL,
            metode_pembayaran VARCHAR(100) NULL,
            budget_per_orang DOUBLE NULL,
            total_estimasi DOUBLE NULL,
            UNIQUE KEY uniq_payment_reservation (reservation_id),
            FOREIGN KEY (reservation_id) REFERENCES `{MYSQL_RESERVATIONS_TABLE}`(reservation_id))"""
        )
        cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS `{MYSQL_REVIEWS_TABLE}` (
            review_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            reservation_id VARCHAR(50) NULL,
            rating DOUBLE NULL,
            catatan_staff TEXT NULL,
            UNIQUE KEY uniq_review_reservation (reservation_id),
            FOREIGN KEY (reservation_id) REFERENCES `{MYSQL_RESERVATIONS_TABLE}`(reservation_id))"""
        )

        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Reservation ID", "reservation_id", "VARCHAR(50) NOT NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Customer ID", "customer_id", "VARCHAR(50) NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Nama Customer", "nama_customer", "VARCHAR(255) NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "No. HP", "phone", "VARCHAR(50) NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Email", "email", "VARCHAR(255) NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Tanggal Reservasi", "tanggal_reservasi", "DATETIME NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Waktu Reservasi", "waktu_reservasi", "VARCHAR(20) NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Durasi (menit)", "durasi_menit", "INT NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Jumlah Orang", "jumlah_orang", "INT NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Area Meja", "area_meja", "VARCHAR(100) NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Tipe Meja", "tipe_meja", "VARCHAR(100) NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Nomor Meja", "table_id", "INT NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Occasion", "occasion", "VARCHAR(100) NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Special Request", "special_request", "TEXT NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Estimasi Budget/Orang (IDR)", "budget_per_orang", "DOUBLE NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Total Estimasi (IDR)", "total_estimasi", "DOUBLE NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Metode Pembayaran", "metode_pembayaran", "VARCHAR(100) NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Channel Booking", "channel_booking", "VARCHAR(100) NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Status Reservasi", "status_reservasi", "VARCHAR(50) NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Rating", "rating", "DOUBLE NULL")
        _rename_column_if_exists(cursor, MYSQL_RESERVATIONS_TABLE,
                                 "Catatan Staff", "catatan_staff", "TEXT NULL")

        _ensure_nullable_column(cursor, MYSQL_CUSTOMERS_TABLE, "phone", "phone VARCHAR(50) NULL")
        _ensure_nullable_column(cursor, MYSQL_CUSTOMERS_TABLE, "email", "email VARCHAR(255) NULL")
        _ensure_nullable_column(cursor, MYSQL_TABLES_TABLE, "area_meja", "area_meja VARCHAR(100) NULL")
        _ensure_nullable_column(cursor, MYSQL_TABLES_TABLE, "tipe_meja", "tipe_meja VARCHAR(100) NULL")
        _ensure_nullable_column(cursor, MYSQL_TABLES_TABLE, "kapasitas", "kapasitas INT NULL")
        _ensure_nullable_column(cursor, MYSQL_RESERVATIONS_TABLE, "customer_id", "customer_id VARCHAR(50) NULL")
        _ensure_nullable_column(cursor, MYSQL_RESERVATIONS_TABLE, "table_id", "table_id INT NULL")
        _ensure_nullable_column(cursor, MYSQL_RESERVATIONS_TABLE, "tanggal_reservasi", "tanggal_reservasi DATETIME NULL")
        _ensure_nullable_column(cursor, MYSQL_RESERVATIONS_TABLE, "durasi_menit", "durasi_menit INT NULL")
        _ensure_nullable_column(cursor, MYSQL_RESERVATIONS_TABLE, "jumlah_orang", "jumlah_orang INT NULL")
        _ensure_nullable_column(cursor, MYSQL_RESERVATIONS_TABLE, "occasion", "occasion VARCHAR(100) NULL")
        _ensure_nullable_column(cursor, MYSQL_RESERVATIONS_TABLE, "special_request", "special_request TEXT NULL")
        _ensure_nullable_column(cursor, MYSQL_RESERVATIONS_TABLE, "status_reservasi", "status_reservasi VARCHAR(50) NULL")
        _ensure_nullable_column(cursor, MYSQL_RESERVATIONS_TABLE, "channel_booking", "channel_booking VARCHAR(100) NULL")
        _ensure_nullable_column(cursor, MYSQL_PAYMENTS_TABLE, "reservation_id", "reservation_id VARCHAR(50) NULL")
        _ensure_nullable_column(cursor, MYSQL_PAYMENTS_TABLE, "metode_pembayaran", "metode_pembayaran VARCHAR(100) NULL")
        _ensure_nullable_column(cursor, MYSQL_PAYMENTS_TABLE, "budget_per_orang", "budget_per_orang DOUBLE NULL")
        _ensure_nullable_column(cursor, MYSQL_PAYMENTS_TABLE, "total_estimasi", "total_estimasi DOUBLE NULL")
        _ensure_nullable_column(cursor, MYSQL_REVIEWS_TABLE, "reservation_id", "reservation_id VARCHAR(50) NULL")
        _ensure_nullable_column(cursor, MYSQL_REVIEWS_TABLE, "rating", "rating DOUBLE NULL")
        _ensure_nullable_column(cursor, MYSQL_REVIEWS_TABLE, "catatan_staff", "catatan_staff TEXT NULL")

        conn.commit()
        cursor.close()
        conn.close()
        global _SCHEMA_ENSURED
        _SCHEMA_ENSURED = True
        return True, None
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
        ensure_mysql_schema()
        for _, row in df.iterrows():
            record = row.to_dict()
            sync_reservation_to_mysql(record)
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
        # Ensure schema only once per process to avoid repeated ALTER/SHOW calls
        global _SCHEMA_ENSURED
        if not _SCHEMA_ENSURED:
            ensure_mysql_schema()
        cursor = conn.cursor()

        reservation_id = record.get("Reservation ID")
        customer_id = record.get("Customer ID")
        nama_customer = record.get("Nama Customer")
        phone = str(record.get("No. HP", "")).strip() if record.get("No. HP") is not None else None
        email = record.get("Email")
        tanggal_reservasi = record.get("Tanggal Reservasi") or record.get("Tanggal")
        if isinstance(tanggal_reservasi, str) and " " not in tanggal_reservasi and record.get("Waktu Reservasi"):
            tanggal_reservasi = f"{tanggal_reservasi} {record.get('Waktu Reservasi')}"
        durasi_menit = record.get("Durasi (menit)") or record.get("durasi_menit")
        jumlah_orang = record.get("Jumlah Orang") or record.get("jumlah_orang")
        area_meja = record.get("Area Meja")
        tipe_meja = record.get("Tipe Meja")
        table_id = record.get("Nomor Meja") or record.get("table_id")
        occasion = record.get("Occasion")
        special_request = record.get("Special Request")
        status_reservasi = record.get("Status Reservasi")
        channel_booking = record.get("Channel Booking") or record.get("channel_booking")
        metode_pembayaran = record.get("Metode Pembayaran") or record.get("metode_pembayaran")
        budget_per_orang = record.get("Estimasi Budget/Orang (IDR)") or record.get("budget_per_orang")
        total_estimasi = record.get("Total Estimasi (IDR)") or record.get("total_estimasi")
        rating = record.get("Rating")
        catatan_staff = record.get("Catatan Staff") or record.get("catatan_staff")

        if customer_id:
            cursor.execute(
                f"INSERT INTO `{MYSQL_CUSTOMERS_TABLE}` (customer_id, nama_customer, phone, email) VALUES (%s, %s, %s, %s) "
                f"ON DUPLICATE KEY UPDATE nama_customer=VALUES(nama_customer), phone=VALUES(phone), email=VALUES(email)",
                (customer_id, nama_customer, phone, email)
            )

        if table_id is not None:
            kapasitas = _parse_capacity_from_tipe(tipe_meja, jumlah_orang)
            cursor.execute(
                f"INSERT INTO `{MYSQL_TABLES_TABLE}` (table_id, area_meja, tipe_meja, kapasitas) VALUES (%s, %s, %s, %s) "
                f"ON DUPLICATE KEY UPDATE area_meja=VALUES(area_meja), tipe_meja=VALUES(tipe_meja), kapasitas=VALUES(kapasitas)",
                (table_id, area_meja, tipe_meja, kapasitas)
            )

        cursor.execute(
            f"INSERT INTO `{MYSQL_RESERVATIONS_TABLE}` (reservation_id, customer_id, table_id, tanggal_reservasi, durasi_menit, jumlah_orang, occasion, special_request, status_reservasi, channel_booking) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            f"ON DUPLICATE KEY UPDATE customer_id=VALUES(customer_id), table_id=VALUES(table_id), tanggal_reservasi=VALUES(tanggal_reservasi), durasi_menit=VALUES(durasi_menit), jumlah_orang=VALUES(jumlah_orang), occasion=VALUES(occasion), special_request=VALUES(special_request), status_reservasi=VALUES(status_reservasi), channel_booking=VALUES(channel_booking)",
            (reservation_id, customer_id, table_id, tanggal_reservasi, durasi_menit, jumlah_orang, occasion, special_request, status_reservasi, channel_booking)
        )

        if metode_pembayaran or budget_per_orang is not None or total_estimasi is not None:
            cursor.execute(
                f"INSERT INTO `{MYSQL_PAYMENTS_TABLE}` (reservation_id, metode_pembayaran, budget_per_orang, total_estimasi) VALUES (%s, %s, %s, %s) "
                f"ON DUPLICATE KEY UPDATE metode_pembayaran=VALUES(metode_pembayaran), budget_per_orang=VALUES(budget_per_orang), total_estimasi=VALUES(total_estimasi)",
                (reservation_id, metode_pembayaran, budget_per_orang, total_estimasi)
            )

        if rating is not None or catatan_staff is not None:
            cursor.execute(
                f"INSERT INTO `{MYSQL_REVIEWS_TABLE}` (reservation_id, rating, catatan_staff) VALUES (%s, %s, %s) "
                f"ON DUPLICATE KEY UPDATE rating=VALUES(rating), catatan_staff=VALUES(catatan_staff)",
                (reservation_id, rating, catatan_staff)
            )

        conn.commit()
        cursor.close()
        conn.close()
        return True, None
    except Error as e:
        return False, str(e)
    except Exception as exc:
        return False, str(exc)


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


def load_data() -> pd.DataFrame:
    try:
        ensure_mysql_schema()
    except Exception:
        pass

    remote_df = load_mysql_data()
    if remote_df is None:
        return load_local_data()

    if remote_df.empty:
        local_df = load_local_data()
        if not local_df.empty:
            ensure_mysql_schema()
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
        if not DATA_PATH.exists():
            existing = []
        else:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
                if not isinstance(existing, list):
                    existing = []
    except Exception as exc:
        existing = []

    # add metadata for sync status so we can retry later if needed
    record_meta = dict(record)
    record_meta.setdefault("_synced", False)
    existing.append(record_meta)

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

    # Try to sync immediately; update the saved JSON with sync result
    synced, sync_error = sync_reservation_to_mysql(record)
    try:
        # reload to avoid race and update the last appended record's _synced flag
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if not isinstance(existing, list):
            existing = []
        if existing:
            # find the last matching reservation by Reservation ID if present
            rid = record.get("Reservation ID")
            updated = False
            if rid:
                for item in reversed(existing):
                    if item.get("Reservation ID") == rid:
                        item["_synced"] = bool(synced)
                        updated = True
                        break
            if not updated and existing:
                existing[-1]["_synced"] = bool(synced)

            if synced and existing:
                import datetime
                existing[-1]["_synced_at"] = datetime.datetime.utcnow().isoformat()

        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception:
        # ignore JSON write errors here but preserve sync result in return
        pass

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
