import network
import socket
import time

# ---------- Wi-Fi Configuration ----------
SSID = "YOUR_WIFI_SSID"
PASSWORD = "YOUR_WIFI_PASSWORD"

UDP_TARGET_IP = "192.168.50.35"   # Destination device on LAN
UDP_TARGET_PORT = 5006

# ---------- Connect to Wi-Fi ----------
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

if not wlan.isconnected():
    print("Connecting to WiFi...")
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        time.sleep(0.5)

print("Connected to WiFi:", wlan.ifconfig())

# ---------- UDP Socket ----------
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ---------- Main Loop ----------
counter = 0  # First byte counter (0–255)

try:
    while True:
        
        payload = bytes([counter]) + bytes(range(1, 255))+ bytes(range(0, 255))+bytes(range(0, 37))

        print("Sending UDP payload:", list(payload))

        sock.sendto(payload, (UDP_TARGET_IP, UDP_TARGET_PORT))

        counter = (counter + 1) & 0xFF  # Wrap at 255
        time.sleep(0.1)

except KeyboardInterrupt:
    sock.close()
    print("Stopped")

