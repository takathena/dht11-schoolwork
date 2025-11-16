import network
import socket
import time
from machine import Pin
import dht

# ------------------- WiFi Setup -------------------
ssid = "gendis"
password = "sipwes00"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
print("Menghubungkan ke WiFi...")
while not wlan.isconnected():
    time.sleep(1)
print("WiFi connected:", wlan.ifconfig())

# ------------------- DHT11 Setup -------------------
sensor = dht.DHT11(Pin(4))

# ------------------- HTML Dashboard -------------------
html = """
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard ESP32</title>
<link href="https://fonts.cdnfonts.com/css/rubik-2" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: Poppins, sans-serif;
  background: #F3F5F5;
}

header {
  background: #B41F25;
  color: white;
  padding: 15px;
  text-align: center;
  font-size: 1.5em;
}

/* GRID ATAS (4 kolom) */
.dashboard {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  padding: 20px;
}

.card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.15);
  text-align: center;
}

/* GRID BARIS KEDUA (MAP + PIE CHART) */
.row-2 {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 15px;
  padding: 0 20px;
}

.row-2 .card {
  display: flex;
  flex-direction: column;
}

/* MAP fix agar selalu full dalam card */
#map {
  width: 100%;
  height: 100%;
  min-height: 350px;
  flex: 1;
  margin-top: 12px;
  border-radius: 10px;
}

.chart-box {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.15);
}

/* GRID BAWAH */
.bottom {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  padding: 20px;
}
</style>
</head>

<body>
<header>Dashboard Monitoring ESP32</header>

<!-- ====== BARIS ATAS ====== -->
<div class="dashboard">

  <div class="card">
    <div class="card-title">Waktu Realtime</div>
    <div class="card-value" id="time">--:--:--</div>
  </div>

  <div class="card">
    <div class="card-title">Suhu (°C)</div>
    <div class="card-value" id="temp">--</div>
  </div>

  <div class="card">
    <div class="card-title">Kelembapan (%)</div>
    <div class="card-value" id="hum">--</div>
  </div>

  <div class="card">
    <div class="card-title">Status ESP32</div>
    <div class="card-value" style="color:green">Aktif</div>
  </div>

</div>

<!-- ====== BARIS KEDUA (MAP + PIE) ====== -->
<div class="row-2">
  <div class="card">
    <div class="card-title">Lokasi ESP32</div>
    <div id="map"></div>
  </div>

  <div class="chart-box">
    <h3>Diagram Lingkaran</h3>
    <canvas id="pieChart"></canvas>
  </div>
</div>

<!-- ====== BARIS BAWAH (LINE + BAR) ====== -->
<div class="bottom">
  <div class="chart-box">
    <h3>Chart Garis</h3>
    <canvas id="lineChart"></canvas>
  </div>

  <div class="chart-box">
    <h3>Chart Batang</h3>
    <canvas id="barChart"></canvas>
  </div>
</div>

<script>
// waktu realtime
setInterval(()=>{
  document.getElementById('time').textContent = new Date().toLocaleTimeString();
},1000);

// data arrays
let labels=[], tempData=[], humData=[];

// MAP
var map = L.map('map').setView([-8.244916, 112.619749], 15);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19}).addTo(map);
L.marker([-8.244916, 112.619749]).addTo(map).bindPopup("Lokasi ESP32").openPopup();

// memaksa map menghitung ulang ukuran agar fit card
setTimeout(() => { map.invalidateSize(); }, 300);

window.addEventListener('resize', () => map.invalidateSize());

// LINE CHART
const lineCtx=document.getElementById('lineChart').getContext('2d');
let lineChart=new Chart(lineCtx,{
  type:'line',
  data:{
    labels:labels,
    datasets:[
      {label:'Suhu (°C)', data:tempData, borderColor:'#d21919', borderWidth:2, fill:false, tension:0.3},
      {label:'Kelembapan (%)', data:humData, borderColor:'#ffe6e6', borderWidth:2, fill:false, tension:0.3}
    ]
  }
});

// BAR CHART
const barCtx=document.getElementById('barChart').getContext('2d');
let barChart=new Chart(barCtx,{
  type:'bar',
  data:{
    labels:labels,
    datasets:[
      {label:'Suhu', data:tempData, backgroundColor:'#d21919'},
      {label:'Kelembapan', data:humData, backgroundColor:'#ffe6e6'}
    ]
  }
});

// PIE CHART
const pieCtx=document.getElementById('pieChart').getContext('2d');
let pieChart=new Chart(pieCtx,{
  type:'pie',
  data:{
    labels:['Suhu','Kelembapan'],
    datasets:[{
      data:[0,0],
      backgroundColor:['#d21919','#ffe6e6']
    }]
  }
});

// FETCH DATA dari /data
setInterval(async()=>{
  try{
    const r = await fetch('/data');
    const d = await r.json();

    document.getElementById('temp').textContent = d.temp;
    document.getElementById('hum').textContent = d.hum;

    if(labels.length > 10){ labels.shift(); tempData.shift(); humData.shift(); }

    labels.push(new Date().toLocaleTimeString());
    tempData.push(d.temp);
    humData.push(d.hum);

    lineChart.update();
    barChart.update();

    pieChart.data.datasets[0].data = [d.temp, d.hum];
    pieChart.update();

  }catch(e){ console.log(e); }
},2000);

</script>
</body>x
</html>
"""

# ------------------- Web Server -------------------
def web_page():
    return html

def run_server(ip):
    addr = socket.getaddrinfo(ip, 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print("Web server aktif di http://%s" % ip)

    while True:
        conn, addr = s.accept()
        req = conn.recv(1024)
        req = str(req)

        if '/data' in req:
            try:
                sensor.measure()
                temp = sensor.temperature()
                hum = sensor.humidity()
                response = '{{"temp": {:.1f}, "hum": {:.1f}}}'.format(temp, hum)
            except:
                response = '{"temp":0,"hum":0}'

            conn.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n')
            conn.send(response)

        else:
            conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
            conn.sendall(html)

        conn.close()

run_server(wlan.ifconfig()[0])
