import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
import time
import paho.mqtt.publish as publish
import os
st.set_page_config(layout="wide")
st.title("Smart Room Dashboard")

conn = sqlite3.connect("iot.db")
df = pd.read_sql("SELECT * FROM events ORDER BY ts_epoch", conn)

if df.empty:
    st.warning("No data yet")
    st.stop()

df["time"] = pd.to_datetime(df["ts_epoch"], unit="s")

latest = df.iloc[-1]

# ---- METRICS ----
col1, col2, col3, col4 = st.columns(4)

col1.metric("Residents", int(latest["residents"]))
col2.metric("Temperature (°C)", round(latest["temp"], 2))
col3.metric("Pressure", int(latest["pressure"]))
col4.metric("Heater", "ON" if latest["heater_on"] else "OFF")

# ---- CHARTS ----
st.subheader("Temperature Trend")
st.line_chart(df.set_index("time")["temp"])

st.subheader("Occupancy Trend")
st.line_chart(df.set_index("time")["residents"])
# ---- MANUAL CONTROL (DEMO) ----
st.subheader("Manual Controls")

if st.button("Turn Heater ON"):
    publish.single(
        topic="home/commands",
        payload="TURN_HEATER_ON",
        hostname="localhost",
        port=1883
    )
    st.success("Command sent")

if st.button("Turn Heater OFF"):
    publish.single(
        topic="home/commands",
        payload="TURN_HEATER_OFF",
        hostname="localhost",
        port=1883
    )
    st.success("Command sent")

# ---- IMAGE ----
st.subheader("Latest Entry Image")
IMAGE_FOLDER = "/root/images/"


image_files = sorted(
    [os.path.join(IMAGE_FOLDER, f) for f in os.listdir(IMAGE_FOLDER) if f.endswith((".jpg", ".png"))],
    key=os.path.getmtime,
    reverse=True
)[:3]

if image_files:
    cols = st.columns(len(image_files))
    for col, img_path in zip(cols, image_files):
        img = Image.open(img_path)
        img = img.resize((400,250))  
        col.image(img)
else:
    st.info("No images found")