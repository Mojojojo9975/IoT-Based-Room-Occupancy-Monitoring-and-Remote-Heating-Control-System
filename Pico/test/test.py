from machine import Pin, UART
import time

# ---------- UART / RS485 ----------
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

DE_RE_PIN = 4
de_re = Pin(DE_RE_PIN, Pin.OUT)
de_re.value(0)  # Receive mode

# ---------- RS485 Send Function ----------
def rs485_send_bytes(payload, baud=9600):
    de_re.value(1)              # Enable transmit
    time.sleep_us(200)

    uart.write(payload)

    bits = len(payload) * 10    # 8 data + start + stop
    tx_time_ms = (bits * 1000) // baud
    time.sleep_ms(tx_time_ms + 10)

    de_re.value(0)              # Back to receive
    time.sleep_us(50)

# ---------- Main Loop ----------
counter = 0  # First byte counter (0–255)

try:
    while True:
        # First byte = counter, rest = 1..100
        payload = bytes([counter]) + bytes(range(1, 154))

        print("Sending payload:", list(payload))

        rs485_send_bytes(payload)

        counter = (counter + 1) & 0xFF  # Wrap at 255
        #time.sleep(0.1)

except KeyboardInterrupt:
    de_re.value(0)
    print("Stopped")

