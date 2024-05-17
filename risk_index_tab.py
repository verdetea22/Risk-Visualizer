# risk_index_tab.py
import dash
from dash import dcc, html, Input, Output, State, ALL, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import numpy as np
import pandas as pd
from utils import parse_contents
from mitigation import mitigation_strategies  # Ensure utils has the necessary functions

import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from utils import parse_contents

def determine_risk_index(status, threshold):
    range_under_threshold = threshold * 0.10
    if status < threshold:
        return 1  # Low Risk
    elif threshold <= status <= (threshold + range_under_threshold):
        return 2  # Approaching Risk
    else:
        return 3  # High Risk

def process_risk_index(data):
    # Additional data processing can be added here
    return data

def calculate_cumulative_risk_index(df):
    df['Risk Index'] = df.apply(lambda row: determine_risk_index(row['Status'], row['Threshold']), axis=1)
    weighted_risk_indices = {}

    for risk_driver, group in df.groupby('Risk Drivers'):
        priority_vector = group['PV'].to_numpy()
        risk_indices = group['Risk Index'].to_numpy()
        weighted_risk_index = np.dot(priority_vector, risk_indices)
        weighted_risk_indices[risk_driver] = weighted_risk_index

    return weighted_risk_indices

def risk_index_tab_layout():
    return html.Div([
        dcc.Upload(
            id='upload-risk-data',
            children=html.Button('Upload Risk Data', style={'width': '100%', 'height': '50px'}),
            style={'textAlign': 'center', 'padding': '20px'},
            multiple=False
        ),
        html.Div(id='risk-inputs-container'),
        html.Button('Analyze Risk', id='analyze-risk-button', style={'width': '100%', 'height': '50px'}),
        html.Div(id='risk-analysis-container')
    ])

@callback(
    Output('risk-inputs-container', 'children'),
    Input('upload-risk-data', 'contents')
)
def update_risk_inputs(contents):
    if contents:
        df = parse_contents(contents)
        df['Threshold'] = df['Threshold'].astype(float)  # Ensuring proper data type
        return [
            dbc.InputGroup([
                dbc.InputGroupText(row['Sub Risk Drivers']),
                dbc.Input(type="number", placeholder="Enter current status", id={'type': 'risk-status-input', 'index': str(index)}),
                dbc.InputGroupText(f"Threshold: {row['Threshold']} {row['Unit']}", style={'width': '150px'})
            ], style={'margin': '10px'}) for index, row in df.iterrows()
        ]
    return "Please upload risk data file."

@callback(
    Output('risk-analysis-container', 'children'),
    Input('analyze-risk-button', 'n_clicks'),
    State({'type': 'risk-status-input', 'index': ALL}, 'value'),
    State('upload-risk-data', 'contents')
)
def analyze_risk(n_clicks, status_values, contents):
    if n_clicks and contents:
        df = parse_contents(contents)
        df['Status'] = list(map(float, status_values))  # Convert status inputs to float
        df = calculate_cumulative_risk_index(df)  # Now returns a dictionary

        # Visualization (simple example using the calculated risk indices)
        data = [{"Risk Driver": key, "Weighted Risk Index": value} for key, value in df.items()]
        fig = px.bar(data, x='Risk Driver', y='Weighted Risk Index', title="Cumulative Risk Index by Driver")
        return dcc.Graph(figure=fig)

    return "No data to analyze. Please upload data and set statuses."