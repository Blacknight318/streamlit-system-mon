import psutil
import streamlit as st
import time
import pandas as pd
import plotly.express as px


st.title("System Monitor")
# Setting up columns for better display on wide screen
cpu_plot = st.empty()
columns_placeholder = st.empty()


# Create an empty dataframe to store the metrics
metrics_df = pd.DataFrame(columns=["Timestamp", "CPU", "Memory", "Disk", "Temperature"])


def get_metrics():
    # Get current timestamp
    timestamp = pd.Timestamp.now()

    # Get CPU usage
    cpu_usage = psutil.cpu_percent()

    # Get memory usage
    memory_usage = psutil.virtual_memory().percent

    # Get disk usage
    disk_usage = psutil.disk_usage("/").percent

    # Get Temperature Metric
    temperatures = psutil.sensors_temperatures()

    # Extract Specified Temperature
    temperature = None
    if "coretemp" in temperatures:
        coretemp_temps = temperatures["coretemp"]
        for temp in coretemp_temps:
            if temp.label == "Package id 0":
                temperature = temp.current
                break

    return timestamp, cpu_usage, memory_usage, disk_usage, temperature


def main():
    # Polling initial data
    timestamp, cpu_usage, memory_usage, disk_usage, temperature = get_metrics()

    # Append current metrics to the dataframe
    metrics_df.loc[len(metrics_df)] = [timestamp, cpu_usage, memory_usage, disk_usage, temperature]

    # Keep only the most recent 3600 data points
    metrics_df_trimmed = metrics_df[-86400:]

    # ---Updating display elements---
    # Plotting all three metrics
    cpu_fig = px.line(
        metrics_df_trimmed, x="Timestamp",
        y=["CPU", "Memory", "Disk", "Temperature"],
        title="CPU Usage",
        labels={
            "CPU": "%",
            "Memory": "%",
            "Disk": "%",
            "Temperature": "Temperature (°C)"
            }
    )
    cpu_plot.plotly_chart(cpu_fig)

    # Columns for metrics
    with columns_placeholder:
        cpu_col, memory_col, disk_col, temp_col = st.columns(4)

        # CPU Metrics
        cpu_col.metric("CPU Usage", cpu_usage)

        # Memory metrics
        memory_col.metric("Memory Usage", memory_usage)

        # Disk metrics
        disk_col.metric("Disk Usage", disk_usage)


        # Temperature Metrics
        temp_col.metric("Package id 0", temperature)


if __name__ == "__main__":
    while True:
        main()
        time.sleep(1)
