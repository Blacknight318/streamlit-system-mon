import psutil
import sqlite3
from datetime import datetime
import time


# Connect to SQLite database and create metrics table if it doesn't exist
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

while True:
    timestamp = datetime.now()
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

    cursor.execute('''
        INSERT INTO metrics (timestamp, cpu, memory, disk, temperature)
        VALUES (?, ?, ?, ?, ?)
    ''', (timestamp, cpu_usage, memory_usage, disk_usage, temperature))
    conn.commit()
    
    time.sleep(1)
