from utils import load_local_data, load_mysql_data
for name, fn in [('local', load_local_data), ('mysql', load_mysql_data)]:
    df = fn()
    print(name, 'rows', 'None' if df is None else len(df))
    if df is not None and not df.empty:
        print('min', df['Tanggal Reservasi'].min())
        print('max', df['Tanggal Reservasi'].max())
        print(df[['Reservation ID','Tanggal Reservasi']].head(5).to_dict(orient='records'))

