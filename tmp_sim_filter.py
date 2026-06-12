from utils import load_local_data, load_mysql_data
import pandas as pd

df_all = load_mysql_data()
if df_all is None or df_all.empty:
    df_all = load_local_data()

# parse date column like page
if 'Tanggal Reservasi' in df_all.columns:
    if not pd.api.types.is_datetime64_any_dtype(df_all['Tanggal Reservasi']):
        df_all['Tanggal Reservasi'] = pd.to_datetime(df_all['Tanggal Reservasi'], errors='coerce')
elif 'Tanggal' in df_all.columns:
    df_all['Tanggal Reservasi'] = pd.to_datetime(df_all['Tanggal'], errors='coerce')
else:
    df_all['Tanggal Reservasi'] = pd.NaT

min_date = df_all['Tanggal Reservasi'].min().date() if not df_all['Tanggal Reservasi'].isna().all() else pd.Timestamp.today().date()
max_date = df_all['Tanggal Reservasi'].max().date() if not df_all['Tanggal Reservasi'].isna().all() else pd.Timestamp.today().date()
print('min_date', min_date, 'max_date', max_date)
filtered = df_all[(df_all['Tanggal Reservasi'].dt.date >= min_date) & (df_all['Tanggal Reservasi'].dt.date <= max_date)]
print('filtered rows', len(filtered))

