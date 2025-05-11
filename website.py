from flask import Flask
from pyngrok import ngrok
from threading import Thread
from dash import Dash, html, dash_table, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import os
import random

PORT = random.randint(1024, 65535)

# Initialize Flask and Dash
server = Flask(__name__)
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], server=server)
app.title = "OMARSHMB.mark1"

# Load data from file
def load_data():
    df = pd.DataFrame({ "Stock Name": []})
    try:
        file_path = "positions.txt"
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, header=None) 
            df.columns = ["Stock Name"]
    except pd.errors.EmptyDataError:
        pass
    return df

# Function to get CPU temperature
def get_pi_temperature():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        temp = int(f.read()) / 1000.0  # Convert from millidegrees to degrees Celsius
    return round(temp, 2)

# Navbar with temperature display
navbar = dbc.Navbar(
    dbc.Container([
        dbc.Row([
            dbc.Col(html.Img(src="assets/logo.jpg", height="40px", style={"borderRadius": "50%"}), width="auto"),
            dbc.Col(dbc.NavbarBrand("Trading Bot OMARSHMB.mark1", className="ms-3", style={"fontSize": "24px", "fontWeight": "bold"}), width="auto")
        ], align="center", className="g-0"),
        dbc.Col(html.Div(id="pi-temp", className="text-white", style={"fontSize": "18px", "fontWeight": "bold"}), width="auto", className="ms-auto")
    ]),
    style={"background": "linear-gradient(90deg, #ff4b2b, #ffb900)"},
    dark=True,
    className="mb-4"
)

# Table
table = dash_table.DataTable(
    id="stock-table",
    columns=[{"name": col, "id": col} for col in load_data().columns],
    data=load_data().to_dict("records"),
    style_table={"overflowX": "auto", "border": "2px solid #000", "borderRadius": "10px"},
    style_header={"backgroundColor": "#1c5858", "fontWeight": "bold", "color": "white", "fontSize": "16px", "textAlign": "center"},
    style_cell={"backgroundColor": "#212529", "color": "white", "padding": "12px", "textAlign": "center", "border": "1px solid #444"},
    style_data={"border": "1px solid #555"}
)

# Layout
app.layout = dbc.Container([
    navbar,
    html.H2("Current Positions", className="text-white mb-4", style={"textAlign": "center"}),
    dbc.Button("Refresh Data", id="refresh-button", color="secondary", className="mb-3", style={"fontSize": "18px", "padding": "10px 20px", "borderRadius": "8px"}),
    table
], fluid=True)


# Callbacks
@app.callback(
    Output("stock-table", "data"),
    Input("refresh-button", "n_clicks")
)
def update_table(n_clicks):
    return load_data().to_dict("records")

@app.callback(
    Output("pi-temp", "children"),
    Input("refresh-button", "n_clicks")
)
def update_temperature(n_clicks):
    return f"Board Temp: {get_pi_temperature()}"

# Start ngrok tunnel
def start_ngrok():
    url = ngrok.connect(PORT).public_url
    print(f"Public URL: {url}")

Thread(target=start_ngrok, daemon=True).start()

# Run the app
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=PORT)
