import machine
from machine import Pin, UART, time_pulse_us
from bmp280 import BMP280
import time

# ---------- UART / RS485 ----------
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
DE_RE_PIN = 4
de_re = Pin(DE_RE_PIN, Pin.OUT)
de_re.value(0)

# ---------- Ultrasonic ----------
TRIGGER_PIN = 3
ECHO_PIN = 2
trigger = Pin(TRIGGER_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)

# ---------- Door Switch ----------
DOOR_PIN = 14
door = Pin(DOOR_PIN, Pin.IN, Pin.PULL_UP)

# ---------- BMP280 ----------
i2c = machine.I2C(0, sda=Pin(20), scl=Pin(21))
bmp = BMP280(i2c)

# ---------- Functions ----------
def get_distance():
    trigger.low()
    time.sleep_us(2)
    trigger.high()
    time.sleep_us(10)
    trigger.low()
    duration = time_pulse_us(echo, 1, 30000)
    if duration < 0:
        return None
    return (duration / 2) * 0.0343

def rs485_send_bytes(payload, baud=9600):
    de_re.value(1)
    time.sleep_us(200)
    uart.write(payload)
    bits = len(payload) * 10
    tx_time_ms = (bits * 1000) // baud
    time.sleep_ms(tx_time_ms + 10)
    de_re.value(0)
    time.sleep_us(50)

# ---------- Main loop ----------
try:
    while True:
        # ---- Distance ----
        dist = get_distance()
        if dist is None:
            d_int, d_frac = 255, 255
        else:
            d_int = int(dist)
            d_frac = int(round((dist - d_int) * 100))
            if d_frac >= 100:
                d_int += 1
                d_frac = 0
            d_int = max(0, min(255, d_int))
            d_frac = max(0, min(99, d_frac))

        # ---- Temperature ----
        temp = bmp.temperature
        t_int = int(temp)
        t_frac = int(round((temp - t_int) * 100))
        t_int = max(0, min(85, t_int))
        t_frac = max(0, min(99, t_frac))

        # ---- Pressure ----
        pressure_pa = int(bmp.pressure)
        pressure_scaled = pressure_pa // 10
        p_hi = (pressure_scaled >> 8) & 0xFF
        p_lo = pressure_scaled & 0xFF

        # ---- Door state ----
        # 0 = closed, 1 = open
        door_state = door.value()

        # ---- Payload (7 bytes) ----
        payload = bytes([
            d_int, d_frac,
            t_int, t_frac,
            p_hi, p_lo,
            door_state
        ])

        print(
            f"D={d_int}.{d_frac:02d}cm "
            f"T={t_int}.{t_frac:02d}C "
            f"P={pressure_pa}Pa "
            f"Door={'OPEN' if door_state else 'CLOSED'} "
            f"-> {list(payload)}"
        )

        rs485_send_bytes(payload)
        time.sleep(0.5)

except KeyboardInterrupt:
    de_re.value(0)
    print("Stopped")

