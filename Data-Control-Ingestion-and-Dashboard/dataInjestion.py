import re
import json
import time
import sqlite3
from paho.mqtt.client import Client
import paho.mqtt.publish as publish

TEMP_THRESHOLD = 20.0
conn = sqlite3.connect("iot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS events (
    ts_epoch REAL,
    residents INTEGER,
    temp REAL,
    pressure INTEGER,
    door_open INTEGER,
    heater_on INTEGER
)
""")
conn.commit()

def on_message(client, userdata, msg):
    raw = msg.payload
    try:
        
        s = raw.decode(errors="ignore")

        
        json_matches = re.findall(r'\{[^{}]*\}', s)
        if not json_matches:
            print("No JSON found in payload:", s)
            return

        for json_str in json_matches:
            try:
                data = json.loads(json_str)

                ts = time.time()
                residents = data.get("residents", 0)
                temp = data.get("temp", 0)
                pressure = data.get("pressure", 0)
                door_open = int(data.get("is_door_open", 0))
                heater_on = int(data.get("is_heater_on", 0))

                cur.execute(
                    "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
                    (ts, residents, temp, pressure, door_open, heater_on)
                )
                conn.commit()

                
                if temp < TEMP_THRESHOLD and not data.get("is_heater_on", False):
                    publish.single(
                        topic="home/commands",
                        payload="TURN_HEATER_ON",
                        hostname="localhost",
                        port=1883
                    )
                    print("Command sent: TURN_HEATER_ON")

            except json.JSONDecodeError as e:
                print("JSON decode error:", e, "String:", json_str)

    except Exception as e:
        print("General parsing error:", e)
        print("RAW DATA:", raw)
