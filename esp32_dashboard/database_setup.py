import sqlite3

# Buat atau sambungkan ke database
conn = sqlite3.connect('data_jarak.db')

# Buat tabel untuk menyimpan data jarak
conn.execute('''
CREATE TABLE IF NOT EXISTS jarak (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    nilai REAL
)
''')

print("Database dan tabel berhasil dibuat!")
conn.close()
