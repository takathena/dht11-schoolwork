import network
import socket
import time
from machine import Pin
import dht

# ------------------- WiFi Setup -------------------
ssid = "Hotspot-SMK"
password = ""

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
html = """<!DOCTYPE html>
<html lang='id'>
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1.0'>
<title>Dashboard DHT11 Telkomsel</title>
<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
<style>
body {
  margin: 0;
  font-family: Poppins, sans-serif;
  background: #f8f8f8;
  color: #333;
}
header {
  background: #e60012;
  color: white;
  text-align: center;
  padding: 15px;
  font-size: 1.5em;
  font-weight: bold;
}
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}
.top-section, .bottom-section {
  display: flex;
  justify-content: center;
  align-items: stretch;
  gap: 20px;
  width: 90%;
  max-width: 1300px;
  margin-bottom: 30px;
  flex-wrap: wrap;
}
.widget {
  flex: 1 1 calc(20% - 20px);
  background: white;
  border-radius: 15px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 4px 10px rgba(0,0,0,0.15);
  transition: transform 0.2s;
  min-width: 200px;
}
.widget:hover {
  transform: scale(1.03);
}
.widget h2 {
  font-size: 1em;
  color: #e60012;
  margin-bottom: 10px;
}
.widget p {
  font-size: 1.8em;
  margin: 0;
}
.active {
  color: green;
  font-weight: bold;
}
.chart-box {
  flex: 1 1 calc(50% - 20px);
  background: white;
  border-radius: 15px;
  padding: 20px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.15);
  min-width: 400px;
}
canvas {
  width: 100% !important;
  height: 350px !important;
}
@media(max-width: 900px) {
  .top-section, .bottom-section {
    flex-direction: column;
    align-items: center;
  }
  .widget, .chart-box {
    width: 90%;
  }
}
</style>
</head>
<body>
<header>Dashboard Sensor DHT11</header>
<div class='container'>
  <div class='top-section'>
    <div class='widget'><h2>Suhu (°C)</h2><p id='temp'>--</p></div>
    <div class='widget'><h2>Humidity (%)</h2><p id='hum'>--</p></div>
    <div class='widget'><h2>Avg Suhu</h2><p id='avgTemp'>--</p></div>
    <div class='widget'><h2>Status ESP</h2><p id='status' class='active'>Aktif</p></div>
    <div class='widget'><h2>Waktu & Tempat</h2><p id='location'>Lab Merah<br><span id='time'>--:--:--</span></p></div>
  </div>
  <div class='bottom-section'>
    <div class='chart-box'>
      <h3 style='text-align:center;color:#e60012;'>Diagram Batang</h3>
      <canvas id='barChart'></canvas>
    </div>
    <div class='chart-box'>
      <h3 style='text-align:center;color:#e60012;'>Diagram Garis</h3>
      <canvas id='lineChart'></canvas>
    </div>
  </div>
</div>

<script>
let tempData=[],humData=[],labels=[];
const barCtx=document.getElementById('barChart').getContext('2d');
const lineCtx=document.getElementById('lineChart').getContext('2d');
const barChart=new Chart(barCtx,{type:'bar',data:{labels:labels,datasets:[
{label:'Suhu (°C)',data:tempData,backgroundColor:'#e60012'},
{label:'Kelembapan (%)',data:humData,backgroundColor:'#999'}]},
options:{responsive:true,maintainAspectRatio:false}});
const lineChart=new Chart(lineCtx,{type:'line',data:{labels:labels,datasets:[
{label:'Suhu (°C)',data:tempData,borderColor:'#e60012',fill:false,tension:0.3},
{label:'Kelembapan (%)',data:humData,borderColor:'#999',fill:false,tension:0.3}]},
options:{responsive:true,maintainAspectRatio:false}});
setInterval(()=>{const now=new Date();
document.getElementById('time').textContent=now.toLocaleTimeString();},1000);
setInterval(async()=>{try{
const r=await fetch('/data');const d=await r.json();
document.getElementById('temp').textContent=d.temp;
document.getElementById('hum').textContent=d.hum;
document.getElementById('avgTemp').textContent=d.avg;
if(tempData.length>10){tempData.shift();humData.shift();labels.shift();}
tempData.push(d.temp);humData.push(d.hum);labels.push(new Date().toLocaleTimeString());
barChart.update();lineChart.update();
}catch(e){console.log(e);}},2000);
</script>
</body>
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

    readings = []
    while True:
        conn, addr = s.accept()
        req = conn.recv(1024)
        req = str(req)
        if '/data' in req:
            try:
                sensor.measure()
                temp = sensor.temperature()
                hum = sensor.humidity()
                readings.append(temp)
                if len(readings) > 10: readings.pop(0)
                avg = sum(readings) / len(readings)
                response = '{{"temp": {:.1f}, "hum": {:.1f}, "avg": {:.1f}}}'.format(temp, hum, avg)
            except:
                response = '{"temp":0,"hum":0,"avg":0}'
            conn.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n')
            conn.send(response)
        else:
            conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
            conn.sendall(html)
        conn.close()

run_server(wlan.ifconfig()[0])