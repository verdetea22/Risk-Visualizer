import dash
from dash import dcc, Dash, html, Input, Output, State, ALL
import pandas as pd
import plotly.express as px
import numpy as np
import dash_bootstrap_components as dbc
import base64
import io

from utils import parse_contents

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

def create_sliders(df):
    sliders = []
    risk_drivers = df['Risk Drivers'].unique()
    for driver in risk_drivers:
        sub_drivers = df[df['Risk Drivers'] == driver]['Sub Risk Drivers']
        sliders_for_driver = [html.Div([
            html.Label(sub_driver),
            dcc.Slider(
                id={'type': 'dynamic-slider', 'index': f"{driver}-{sub_driver}"},
                min=1,
                max=9,
                step=1,
                value=5,
                marks={i: str(i) for i in range(10)}
            )
        ]) for sub_driver in sub_drivers]
        sliders.append(html.Div([
            html.H3(driver),
            html.Div(sliders_for_driver, style={'border': 'thin lightgrey solid', 'padding': '20px'})
        ]))
    return sliders

def weights_tab_layout():
    return html.Div([
        dcc.Upload(
            id='upload-data',
            children=html.Button('Upload File', style={'width': '100%', 'height': '50px', 'lineHeight': '50px'}),
            style={'textAlign': 'center', 'padding': '20px'},
            multiple=False
        ),
        html.Div("Rank the following sub-risk drivers in terms of their importance to your project, relative to one another:", style={'textAlign': 'center', 'margin': '10px', 'padding': '10px', 'backgroundColor': '#f7f7f7'}),
        html.Div(id='sliders-container'),
        html.Button('Render Graphs', id='render-button', style={'width': '100%', 'height': '50px', 'lineHeight': '50px', 'backgroundColor': '#007BFF', 'color': 'white'}),
        html.Div(id='graphs-container')
    ])

def calculate_priority_vector(matrix):
    # Calculate the eigenvalues and eigenvectors from the pairwise matrix
    eigvals, eigvecs = np.linalg.eig(matrix)
    max_index = eigvals.argmax()  # Find the index of the maximum eigenvalue
    priority_vector = np.abs(eigvecs[:, max_index])  # Take the eigenvector corresponding to the maximum eigenvalue
    priority_vector /= priority_vector.sum()  # Normalize it to sum to 1
    return priority_vector

def create_charts(df):
    charts_dict = {}
    for risk_driver, group_df in df.groupby('Risk Drivers'):
        sub_risk_drivers = group_df['Sub Risk Drivers'].tolist()
        
        # Create a dummy pairwise matrix as an example:
        # This should ideally come from slider values or another method to determine the relative weights.
        sliders = np.random.rand(len(sub_risk_drivers)) + 1  # Simulating slider values
        matrix = np.array([[sliders[i]/sliders[j] for j in range(len(sliders))] for i in range(len(sliders))])
        
        priority_vector = calculate_priority_vector(matrix)
        
        # Create bar chart data
        bar_data = pd.DataFrame({
            'Sub Risk Drivers': sub_risk_drivers,
            'Risk Index': priority_vector
        })
        bar_fig = px.bar(bar_data, x='Sub Risk Drivers', y='Risk Index', title=f'Risk Index - {risk_driver}')
        bar_fig.update_layout(yaxis=dict(range=[0, 1]))

        # Create pie chart data
        pie_data = pd.DataFrame({
            'Sub Risk Drivers': sub_risk_drivers,
            'Priority Vector': priority_vector
        })
        pie_fig = px.pie(pie_data, values='Priority Vector', names='Sub Risk Drivers', title=f'Priority Vector - {risk_driver}')

        # Store figures in a dictionary
        charts_dict[risk_driver] = {'bar_fig': bar_fig, 'pie_fig': pie_fig}

    return charts_dict


@app.callback(
    Output('sliders-container', 'children'),
    Input('upload-data', 'contents')
)
def update_sliders(contents):
    if contents is None:
        return html.Div("Please upload an Excel file.")
    df = parse_contents(contents)
    return create_sliders(df)

@app.callback(
    Output('graphs-container', 'children'),
    Input('render-button', 'n_clicks'),
    State('upload-data', 'contents')
)
@app.callback(
    Output('graphs-container', 'children'),
    Input('render-button', 'n_clicks'),
    State('upload-data', 'contents'),
    prevent_initial_call=True  # Ensure no chart is attempted before any action
)
def render_graphics(n_clicks, contents):
    if not contents:
        return html.Div('No data to display, please upload a file and press render.')

    df = parse_contents(contents)
    charts_dict = create_charts(df)

    # Prepare HTML Div elements containing the charts
    return [
        html.Div([
            html.H3(f"{risk_driver} Analysis"),
            dcc.Graph(figure=charts['bar_fig']),
            dcc.Graph(figure=charts['pie_fig'])
        ]) for risk_driver, charts in charts_dict.items()
    ]