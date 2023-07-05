import psutil
import streamlit as st
import time
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, timedelta


st.title("System Monitor")
cpu_plot = st.empty()
columns_placeholder = st.empty()

conn = sqlite3.connect('system_metrics.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP,
        cpu FLOAT,
        memory FLOAT,
        disk FLOAT,
        temperature FLOAT
    )
''')
conn.commit()


def get_metrics():
    timestamp = pd.Timestamp.now()
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage("/").percent
    temperatures = psutil.sensors_temperatures()
    temperature = None
    if "coretemp" in temperatures:
        coretemp_temps = temperatures["coretemp"]
        for temp in coretemp_temps:
            if temp.label == "Package id 0":
                temperature = temp.current
                break
    return timestamp, cpu_usage, memory_usage, disk_usage, temperature


def save_metrics(timestamp, cpu_usage, memory_usage, disk_usage, temperature):
    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO metrics (timestamp, cpu, memory, disk, temperature)
        VALUES (?, ?, ?, ?, ?)
    ''', (timestamp_str, cpu_usage, memory_usage, disk_usage, temperature))
    conn.commit()


def cleanup_old_metrics():
    thirty_days_ago = datetime.now() - timedelta(days=30)
    cursor.execute('''
        DELETE FROM metrics
        WHERE timestamp < ?
    ''', (thirty_days_ago,))
    conn.commit()


def fetch_metrics():
    cursor.execute('''
        SELECT * FROM metrics
    ''')
    rows = cursor.fetchall()
    columns = ["id", "timestamp", "cpu", "memory", "disk", "temperature"]
    metrics_df = pd.DataFrame(rows, columns=columns)
    return metrics_df


def main():
    timestamp, cpu_usage, memory_usage, disk_usage, temperature = get_metrics()
    save_metrics(timestamp, cpu_usage, memory_usage, disk_usage, temperature)
    cleanup_old_metrics()
    metrics_df = fetch_metrics()

    metrics_df_trimmed = metrics_df[-86400:]

    cpu_fig = px.line(
        metrics_df_trimmed, x="timestamp",
        y=["cpu", "memory", "disk", "temperature"],
        title="CPU Usage",
        labels={
            "timestamp": "Timestamp",
            "cpu": "CPU (%)",
            "memory": "Memory (%)",
            "disk": "Disk (%)",
            "temperature": "Temperature (°C)"
        }
    )
    cpu_plot.plotly_chart(cpu_fig)

    with columns_placeholder:
        cpu_col, memory_col, disk_col, temp_col = st.columns(4)

        cpu_col.metric("CPU Usage", cpu_usage)
        memory_col.metric("Memory Usage", memory_usage)
        disk_col.metric("Disk Usage", disk_usage)
        temp_col.metric("Package id 0", temperature)


if __name__ == "__main__":
    while True:
        main()
        time.sleep(1)
