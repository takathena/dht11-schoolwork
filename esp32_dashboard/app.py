from flask import Flask, render_template, jsonify
import sqlite3, time, threading, requests

app = Flask(__name__)

ESP32_IP = "http://192.168.137.34"  # Ganti sesuai IP ESP32 kamu

# Inisialisasi database
def init_db():
    conn = sqlite3.connect("jarak.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS data_jarak (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nilai REAL,
            waktu TEXT
        )
    """)
    conn.commit()
    conn.close()

# Ambil data dari ESP32 dan simpan ke database
def fetch_from_esp32():
    while True:
        try:
            r = requests.get(ESP32_IP, timeout=3)
            data = r.json()
            nilai = data["jarak_cm"]

            conn = sqlite3.connect("jarak.db")
            c = conn.cursor()
            c.execute("INSERT INTO data_jarak (nilai, waktu) VALUES (?, datetime('now','localtime'))", (nilai,))
            conn.commit()
            conn.close()

            print(f"Data tersimpan: {nilai} cm")
        except Exception as e:
            print("Gagal ambil data:", e)
        time.sleep(2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    conn = sqlite3.connect("jarak.db")
    c = conn.cursor()
    c.execute("SELECT id, nilai, waktu FROM data_jarak ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()

    if rows:
        history = [r[1] for r in rows][::-1]
        avg = sum(history) / len(history)
        result = {
            "jarak": history[-1],
            "rata2": round(avg, 2),
            "history": history,
            "records": [{"id": r[0], "nilai": r[1], "waktu": r[2]} for r in rows[::-1]]
        }
    else:
        result = {"jarak": 0, "rata2": 0, "history": [], "records": []}

    return jsonify(result)

if __name__ == "__main__":
    init_db()
    t = threading.Thread(target=fetch_from_esp32, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000, debug=True)
