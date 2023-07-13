import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from dash.dependencies import Output, Input
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, timedelta
import plotly.graph_objects as go
import time


# Figure template
load_figure_template('CYBORG')

# Connect to SQLite database and retrieve metrics
conn = sqlite3.connect('system_metrics.db')
cursor = conn.cursor()


# Fetch the latest metric
def fetch_latest_metric():
    with sqlite3.connect('system_metrics.db') as conn:  # Added 'with' statement
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM metrics
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        row = cursor.fetchone()
        columns = ["id", "timestamp", "cpu", "memory", "disk", "temperature"]
        latest_metric = pd.DataFrame([row], columns=columns)
    return latest_metric

# Fetch metrics from the last hour
def fetch_metrics_last_hour():
    with sqlite3.connect('system_metrics.db') as conn:  # Added 'with' statement
        cursor = conn.cursor()
        one_hour_ago = datetime.now() - timedelta(hours=1)
        cursor.execute('''
            SELECT timestamp, cpu, memory, disk, temperature
            FROM metrics
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 3600
        ''', (one_hour_ago,))
        rows = cursor.fetchall()
        columns = ["timestamp", "cpu", "memory", "disk", "temperature"]
        metrics_df = pd.DataFrame(rows, columns=columns)
    return metrics_df


# Create dial gauge for a metric
def create_dial_gauge(metric_name, metric_value):
    symbol = ""
    if metric_name == "CPU Usage":
        symbol = "%"
    elif metric_name == "Memory Usage":
        symbol = "%"
    elif metric_name == "Disk Usage":
        symbol = "%"
    elif metric_name == "Temperature":
        symbol = "°C"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=metric_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': metric_name},
        gauge={'axis': {'range': [None, 100]}},
        number={'suffix': symbol}
    ))
    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        template="plotly_dark"
        )
    return fig


# Create line graph for the last hour of metrics
def create_metrics_graph(metrics_df):
    fig = px.line(metrics_df, x="timestamp", y=["cpu", "memory", "disk", "temperature"])
    # fig.update_traces(
        # name=["CPU Usage", "Memory Usage", "Disk Usage", "Temperature"],
        # hovertemplate='Metric: %{name}<br>Value: %{y}'
    # )
    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Timestamp",
        yaxis_title="%/°C",
        legend_title="Legend"
        )
    return fig


# Fetch the initial data
latest_metric = fetch_latest_metric()
metrics_df = fetch_metrics_last_hour()


# Create the Dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])


# Define the layout of your dashboard
app.layout = dbc.Container([
    html.H1("System Vitals", style={'text-align': 'center'}),
    dbc.Row([
        dbc.Col(
            dcc.Graph(
                id='cpu-gauge',
                figure=create_dial_gauge("CPU Usage", latest_metric["cpu"].iloc[0])
            ),
            width=3
        ),
        dbc.Col(
            dcc.Graph(
                id='memory-gauge',
                figure=create_dial_gauge("Memory Usage", latest_metric["memory"].iloc[0])
            ),
            width=3
        ),
        dbc.Col(
            dcc.Graph(
                id='disk-gauge',
                figure=create_dial_gauge("Disk Usage", latest_metric["disk"].iloc[0])
            ),
            width=3
        ),
        dbc.Col(
            dcc.Graph(
                id='temperature-gauge',
                figure=create_dial_gauge("Temperature", latest_metric["temperature"].iloc[0])
            ),
            width=3
        )
    ], style={'margin-bottom': '20px'}),
    dcc.Graph(
        id='metrics-graph',
        figure=create_metrics_graph(metrics_df)
    ),
        dcc.Interval(
        id='interval-component',
        interval=1000,  # Refresh interval in milliseconds
        n_intervals=0
    )
])


@app.callback(
    [Output('cpu-gauge', 'figure'),
     Output('memory-gauge', 'figure'),
     Output('disk-gauge', 'figure'),
     Output('temperature-gauge', 'figure'),
     Output('metrics-graph', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_data(n):
    # Fetch the latest metric
    latest_metric = fetch_latest_metric()

    # Fetch metrics from the last hour
    metrics_df = fetch_metrics_last_hour()

    # Update the dial gauges
    cpu_gauge = create_dial_gauge("CPU Usage", latest_metric["cpu"].iloc[0])
    memory_gauge = create_dial_gauge("Memory Usage", latest_metric["memory"].iloc[0])
    disk_gauge = create_dial_gauge("Disk Usage", latest_metric["disk"].iloc[0])
    temperature_gauge = create_dial_gauge("Temperature", latest_metric["temperature"].iloc[0])

    # Update the line graph
    metrics_graph = create_metrics_graph(metrics_df)

    return cpu_gauge, memory_gauge, disk_gauge, temperature_gauge, metrics_graph


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True)
