import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from mysql.connector import Error

from utils import (
    _parse_capacity_from_tipe,
    ensure_mysql_schema,
    get_mysql_connection,
    load_local_data,
    MYSQL_CUSTOMERS_TABLE,
    MYSQL_TABLES_TABLE,
    MYSQL_RESERVATIONS_TABLE,
    MYSQL_PAYMENTS_TABLE,
    MYSQL_REVIEWS_TABLE,
)

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR / "data.json"
BATCH_SIZE = 50


def _normalize_value(value: Any) -> Optional[Any]:
    if value is None:
        return None
    if isinstance(value, float) and value != value:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _chunked(records: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    for i in range(0, len(records), size):
        yield records[i : i + size]


def _prepare_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    reservation_id = _normalize_value(raw.get("Reservation ID"))
    customer_id = _normalize_value(raw.get("Customer ID"))
    nama_customer = _normalize_value(raw.get("Nama Customer"))
    phone = _normalize_value(raw.get("No. HP"))
    if phone is not None:
        phone = str(phone).strip()
        if phone == "":
            phone = None
    email = _normalize_value(raw.get("Email"))
    tanggal_reservasi = _normalize_value(raw.get("Tanggal Reservasi") or raw.get("Tanggal"))
    waktu_reservasi = _normalize_value(raw.get("Waktu Reservasi"))
    if isinstance(tanggal_reservasi, str) and " " not in tanggal_reservasi and waktu_reservasi:
        tanggal_reservasi = f"{tanggal_reservasi} {waktu_reservasi}"

    durasi_menit = _normalize_value(raw.get("Durasi (menit)") or raw.get("durasi_menit"))
    jumlah_orang = _normalize_value(raw.get("Jumlah Orang") or raw.get("jumlah_orang"))
    area_meja = _normalize_value(raw.get("Area Meja"))
    tipe_meja = _normalize_value(raw.get("Tipe Meja"))
    table_id = _normalize_value(raw.get("Nomor Meja") or raw.get("table_id"))
    occasion = _normalize_value(raw.get("Occasion"))
    special_request = _normalize_value(raw.get("Special Request"))
    status_reservasi = _normalize_value(raw.get("Status Reservasi"))
    channel_booking = _normalize_value(raw.get("Channel Booking") or raw.get("channel_booking"))
    metode_pembayaran = _normalize_value(raw.get("Metode Pembayaran") or raw.get("metode_pembayaran"))
    budget_per_orang = _normalize_value(raw.get("Estimasi Budget/Orang (IDR)") or raw.get("budget_per_orang"))
    total_estimasi = _normalize_value(raw.get("Total Estimasi (IDR)") or raw.get("total_estimasi"))
    rating = _normalize_value(raw.get("Rating") or raw.get("rating"))
    catatan_staff = _normalize_value(raw.get("Catatan Staff") or raw.get("catatan_staff"))

    kapasitas = None
    if table_id is not None:
        kapasitas = _parse_capacity_from_tipe(tipe_meja, jumlah_orang)

    return {
        "reservation_id": reservation_id,
        "customer_id": customer_id,
        "nama_customer": nama_customer,
        "phone": phone,
        "email": email,
        "tanggal_reservasi": tanggal_reservasi,
        "durasi_menit": durasi_menit,
        "jumlah_orang": jumlah_orang,
        "area_meja": area_meja,
        "tipe_meja": tipe_meja,
        "table_id": table_id,
        "occasion": occasion,
        "special_request": special_request,
        "status_reservasi": status_reservasi,
        "channel_booking": channel_booking,
        "metode_pembayaran": metode_pembayaran,
        "budget_per_orang": budget_per_orang,
        "total_estimasi": total_estimasi,
        "rating": rating,
        "catatan_staff": catatan_staff,
        "kapasitas": kapasitas,
    }


def _batch_insert(cursor, chunk: List[Dict[str, Any]]) -> None:
    customers: Dict[str, Tuple[Any, Any, Any, Any]] = {}
    tables: Dict[int, Tuple[Any, Any, Any, Any]] = {}
    reservations: List[Tuple[Any, ...]] = []
    payments: List[Tuple[Any, Any, Any, Any]] = []
    reviews: List[Tuple[Any, Any, Any]] = []

    for raw in chunk:
        record = _prepare_record(raw)
        reservation_id = record["reservation_id"]
        customer_id = record["customer_id"]
        table_id = record["table_id"]

        if customer_id:
            customers[customer_id] = (
                customer_id,
                record["nama_customer"],
                record["phone"],
                record["email"],
            )

        if table_id is not None:
            tables[table_id] = (
                table_id,
                record["area_meja"],
                record["tipe_meja"],
                record["kapasitas"],
            )

        reservations.append(
            (
                reservation_id,
                customer_id,
                table_id,
                record["tanggal_reservasi"],
                record["durasi_menit"],
                record["jumlah_orang"],
                record["occasion"],
                record["special_request"],
                record["status_reservasi"],
                record["channel_booking"],
            )
        )

        if record["metode_pembayaran"] is not None or record["budget_per_orang"] is not None or record["total_estimasi"] is not None:
            payments.append(
                (
                    reservation_id,
                    record["metode_pembayaran"],
                    record["budget_per_orang"],
                    record["total_estimasi"],
                )
            )

        if record["rating"] is not None or record["catatan_staff"] is not None:
            reviews.append(
                (
                    reservation_id,
                    record["rating"],
                    record["catatan_staff"],
                )
            )

    if customers:
        cursor.executemany(
            f"INSERT INTO `{MYSQL_CUSTOMERS_TABLE}` (customer_id, nama_customer, phone, email) VALUES (%s, %s, %s, %s) "
            f"ON DUPLICATE KEY UPDATE nama_customer=VALUES(nama_customer), phone=VALUES(phone), email=VALUES(email)",
            list(customers.values()),
        )

    if tables:
        cursor.executemany(
            f"INSERT INTO `{MYSQL_TABLES_TABLE}` (table_id, area_meja, tipe_meja, kapasitas) VALUES (%s, %s, %s, %s) "
            f"ON DUPLICATE KEY UPDATE area_meja=VALUES(area_meja), tipe_meja=VALUES(tipe_meja), kapasitas=VALUES(kapasitas)",
            list(tables.values()),
        )

    if reservations:
        cursor.executemany(
            f"INSERT INTO `{MYSQL_RESERVATIONS_TABLE}` (reservation_id, customer_id, table_id, tanggal_reservasi, durasi_menit, jumlah_orang, occasion, special_request, status_reservasi, channel_booking) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            f"ON DUPLICATE KEY UPDATE customer_id=VALUES(customer_id), table_id=VALUES(table_id), tanggal_reservasi=VALUES(tanggal_reservasi), durasi_menit=VALUES(durasi_menit), jumlah_orang=VALUES(jumlah_orang), occasion=VALUES(occasion), special_request=VALUES(special_request), status_reservasi=VALUES(status_reservasi), channel_booking=VALUES(channel_booking)",
            reservations,
        )

    if payments:
        cursor.executemany(
            f"INSERT INTO `{MYSQL_PAYMENTS_TABLE}` (reservation_id, metode_pembayaran, budget_per_orang, total_estimasi) VALUES (%s, %s, %s, %s) "
            f"ON DUPLICATE KEY UPDATE metode_pembayaran=VALUES(metode_pembayaran), budget_per_orang=VALUES(budget_per_orang), total_estimasi=VALUES(total_estimasi)",
            payments,
        )

    if reviews:
        cursor.executemany(
            f"INSERT INTO `{MYSQL_REVIEWS_TABLE}` (reservation_id, rating, catatan_staff) VALUES (%s, %s, %s) "
            f"ON DUPLICATE KEY UPDATE rating=VALUES(rating), catatan_staff=VALUES(catatan_staff)",
            reviews,
        )


def _load_json_records() -> List[Dict[str, Any]]:
    if DATA_PATH.exists():
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def main(batch_size: int = BATCH_SIZE) -> int:
    try:
        ok, err = ensure_mysql_schema()
        if not ok:
            print(f"Schema error: {err}")
            return 1
    except Exception as exc:
        print(f"Schema validation failed: {exc}")
        return 1

    records = _load_json_records()
    if not records:
        print("Tidak ada data di data.json untuk diekspor.")
        return 0

    conn = get_mysql_connection()
    if conn is None:
        print("Gagal terhubung ke MySQL Railway.")
        return 1

    try:
        cursor = conn.cursor()
        total_exported = 0
        for chunk in _chunked(records, batch_size):
            _batch_insert(cursor, chunk)
            conn.commit()
            total_exported += len(chunk)
            print(f"Batch diekspor: {len(chunk)} baris (total {total_exported})")
        cursor.close()
        print(f"Selesai. Total baris diekspor: {total_exported}")
        return 0
    except Error as exc:
        print(f"Error MySQL saat ekspor: {exc}")
        return 1
    except Exception as exc:
        print(f"Error saat ekspor: {exc}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export data.json ke Railway MySQL dalam batch.")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Ukuran batch insert MySQL")
    args = parser.parse_args()

    raise SystemExit(main(batch_size=args.batch_size))
