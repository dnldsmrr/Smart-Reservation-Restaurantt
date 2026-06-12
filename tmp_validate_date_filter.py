from utils import load_mysql_data, load_local_data
import pandas as pd

# simulate page load

df_all = load_mysql_data()
if df_all is None or df_all.empty:
    df_all = load_local_data()

if 'Tanggal Reservasi' in df_all.columns:
    if not pd.api.types.is_datetime64_any_dtype(df_all['Tanggal Reservasi']):
        df_all['Tanggal Reservasi'] = pd.to_datetime(df_all['Tanggal Reservasi'], errors='coerce')
elif 'Tanggal' in df_all.columns:
    df_all['Tanggal Reservasi'] = pd.to_datetime(df_all['Tanggal'], errors='coerce')
else:
    df_all['Tanggal Reservasi'] = pd.NaT

print('rows', len(df_all))
print('has Tanggal Reservasi', 'Tanggal Reservasi' in df_all.columns)
print('dtype', df_all['Tanggal Reservasi'].dtype)
print('min', df_all['Tanggal Reservasi'].min(), 'max', df_all['Tanggal Reservasi'].max())

