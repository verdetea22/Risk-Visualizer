#weights_tab.py
import dash
from dash import dcc, html, Input, Output, State, ALL, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import numpy as np
import pandas as pd
from utils import parse_contents
from mitigation import mitigation_strategies

def process_weights_data(inputs):
    # Example: Return the inputs as processed data, or perform some calculations.
    processed_data = {'processed_data': inputs}  # Mock processing
    return processed_data

# Function to calculate priority vector from pairwise matrix
def calculate_priority_vector(matrix):
    eigvals, eigvecs = np.linalg.eig(matrix)
    max_index = eigvals.argmax()
    priority_vector = np.abs(eigvecs[:, max_index])
    priority_vector /= priority_vector.sum()
    return priority_vector

# Function to create bar and pie charts
def create_charts(df, slider_values_dict):
    charts_dict = {}
    for risk_driver, group_df in df.groupby('Risk Drivers'):
        sliders = [slider_values_dict.get(f"{risk_driver}-{x}", 1) for x in group_df['Sub Risk Drivers']]
        matrix = np.array([[sliders[i]/sliders[j] for j in range(len(sliders))] for i in range(len(sliders))])
        pv = calculate_priority_vector(matrix)

        bar_data = pd.DataFrame({
            'Sub Risk Drivers': group_df['Sub Risk Drivers'],
            'Risk Index': pv
        })
        bar_fig = px.bar(bar_data, x='Sub Risk Drivers', y='Risk Index', title=f'Risk Index - {risk_driver}')
        bar_fig.update_layout(yaxis=dict(range=[0, 1]))

        pie_data = pd.DataFrame({
            'Sub Risk Drivers': group_df['Sub Risk Drivers'],
            'PV': pv
        })
        pie_fig = px.pie(pie_data, values='PV', names='Sub Risk Drivers', title=f'Priority Vector - {risk_driver}')

        charts_dict[risk_driver] = {'bar_fig': bar_fig, 'pie_fig': pie_fig}
    return charts_dict

def weights_tab_layout():
    return html.Div([
        dcc.Upload(
            id='upload-data',  # Ensure this ID matches exactly in your callback
            children=html.Button('Upload File', style={'width': '100%', 'height': '50px', 'lineHeight': '50px'}),
            style={'textAlign': 'center', 'padding': '20px'},
            multiple=False
        ),
        html.Div("Rank the following sub-risk drivers in terms of their importance to your project, relative to one another:",
                 style={'textAlign': 'center', 'margin': '10px', 'padding': '10px', 'backgroundColor': '#f7f7f7'}),
        html.Div(id='sliders-container'),  # Ensure this ID matches exactly in your callback
        html.Button('Render Graphs', id='render-button', style={'width': '100%', 'height': '50px', 'lineHeight': '50px', 'backgroundColor': '#007BFF', 'color': 'white'}),
        html.Div(id='graphs-container')  # Ensure this ID matches exactly in your callback
    ])

@callback(
    Output('sliders-container', 'children'),
    Input('upload-data', 'contents')
)
def update_sliders(contents):
    if contents:
        df = parse_contents(contents)
        return generate_sliders_layout(df)
    return 'Please upload an Excel file'

def generate_sliders_layout(df):
    sliders = []
    risk_drivers = df['Risk Drivers'].unique()
    for driver in risk_drivers:
        sub_drivers = df[df['Risk Drivers'] == driver]['Sub Risk Drivers']
        sliders_for_driver = [
            html.Div([
                html.Label(sub_driver),
                dcc.Slider(
                    id={'type': 'dynamic-slider', 'index': f"{driver}-{sub_driver}"},
                    min=1,
                    max=9,
                    step=1,
                    value=5,  # Assuming a starting value, adjust as needed
                    marks={i: str(i) for i in range(10)}
                )
            ], style={'padding': '10px'})
            for sub_driver in sub_drivers
        ]
        sliders.append(html.Div([
            html.H3(driver),
            html.Div(sliders_for_driver, style={'border': 'thin lightgrey solid', 'padding': '20px'})
        ]))
    return sliders


@callback(
    Output('graphs-container', 'children'),
    Input('render-button', 'n_clicks'),
    State('upload-data', 'contents'),
    State({'type': 'dynamic-slider', 'index': ALL}, 'value'),
    State({'type': 'dynamic-slider', 'index': ALL}, 'id'),
    prevent_initial_call=True
)
def render_graphics(n_clicks, contents, slider_values, slider_ids):
    if n_clicks and contents:
        df = parse_contents(contents)
        slider_values_dict = {slider['index']: value for slider, value in zip(slider_ids, slider_values)}
        
        charts_dict = create_charts(df, slider_values_dict)
        divs = []

        for risk_driver in df['Risk Drivers'].unique():  # Corrected here
            charts = charts_dict[risk_driver]
            pie_data = charts['pie_fig'].data[0]
            max_value_index = np.argmax(pie_data['values'])
            most_important_sub_driver = pie_data['labels'][max_value_index]
            summary_card = dbc.Card(
                dbc.CardBody([
                    html.H4(f'Most important area for {risk_driver}:', style=CARD_TEXT_STYLE),
                    html.P(f"{most_important_sub_driver} (PV: {pie_data['values'][max_value_index]:.2f})", style=CARD_TEXT_STYLE),
                ]),
                style=CARD_STYLE
            )
            graph_row = dbc.Row([
                dbc.Col(dcc.Graph(figure=charts['bar_fig']), md=6),
                dbc.Col(dcc.Graph(figure=charts['pie_fig']), md=6)
            ], className='mb-4')
            divs.append(html.Div([
                html.H3(f'{risk_driver} Summary', style=TEXT_STYLE),
                summary_card,
                html.H3(f'{risk_driver} Graphics', style=TEXT_STYLE),
                graph_row
            ], style={'margin-bottom': '50px'}))
        return divs
    return html.Div('No data to display, please upload a file and render the graphs.')



dcc.Store(id='weights-data'),
dcc.Store(id='risk-index-data')


@callback(
    Output('weights-data', 'data'),
    Input('render-weights-button', 'n_clicks'),
    State('weights-inputs', 'value')  # Assume you collect inputs from user
)
def update_weights_data(n_clicks, inputs):
    if n_clicks:
        processed_data = process_weights_data(inputs)
        return processed_data
    return dash.no_update


TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#191970',
    'fontSize': '20px'
}

CARD_TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#0074D9',
    'fontSize': '24px'
}

CONTENT_STYLE = {
    'margin-left': '5%',
    'margin-right': '5%',
    'padding': '20px 30px'
}

CARD_STYLE = {
    'padding': '20px',
    'border-radius': '5px',
    'background-color': '#F9F9F9',
    'box-shadow': '2px 2px 2px lightgrey'
}
