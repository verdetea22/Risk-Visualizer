import dash
from dash import Dash, dcc, html, Input, Output, State, ALL, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import json
import plotly.express as px

from utils import parse_contents
from weights_mitigations import create_charts, calculate_priority_vector
from risk_index_status import determine_risk_index, process_risk_index, calculate_cumulative_risk_index

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

app.layout = html.Div([
    dcc.Store(id='stored-data'),
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload File', style={'width': '100%'}),
        style={'textAlign': 'center', 'padding': '20px'},
        multiple=False
    ),
    dcc.Tabs(id='tabs', children=[
        dcc.Tab(label='Weights', value='tab-weights'),
        dcc.Tab(label='Risk Index', value='tab-risk'),
        dcc.Tab(label='Summary & Mitigation', value='tab-summary')
    ]),
    html.Div(id='tabs-content')
])

@app.callback(
    Output('stored-data', 'data'),
    Input('upload-data', 'contents')
)
def handle_file_upload(contents):
    if contents is None:
        return {}
    df = parse_contents(contents)
    return df.to_dict('records')

@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value'),
    State('stored-data', 'data')
)
def render_tab_content(tab, data):
    if data is None:
        return "Please upload data to proceed."
    df = pd.DataFrame(data)
    required_columns = ['Risk Drivers', 'Sub Risk Drivers', 'Threshold', 'Unit']
    if not all(col in df.columns for col in required_columns):
        return f"Required columns are missing. Make sure the following columns are included in the uploaded file: {', '.join(required_columns)}"
    
    if tab == 'tab-weights':
        return create_weight_tab(df)
    elif tab == 'tab-risk':
        return create_risk_tab(df)
    elif tab == 'tab-summary':
        return create_summary_tab(df)
    return "This tab is not yet implemented."
    

def create_weight_tab(df):
    slider_groups = []
    for risk_driver, group in df.groupby('Risk Drivers'):
        sliders = [
            html.Div([
                dcc.Slider(
                    id={'type': 'dynamic-slider', 'index': f"{risk_driver}-{row['Sub Risk Drivers']}"},
                    min=0, max=10, step=1, value=5,
                    marks={i: str(i) for i in range(11)},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Label(row['Sub Risk Drivers'])
            ], style={'margin': '20px'})
            for _, row in group.iterrows()
        ]
        slider_groups.append(html.Div([
            html.H3(risk_driver),
            html.Div(sliders)
        ]))

    # Adding a single render button at the bottom of the page
    slider_groups.append(html.Button('Render Graphs', id='render-all-graphs', className='mt-4', n_clicks=0))
    return html.Div(slider_groups)



def create_risk_tab(df):
    content = []
    for name, group in df.groupby('Risk Drivers'):
        rows = [
            dbc.Row([
                dbc.Col(html.Div(f"{row['Sub Risk Drivers']} (Threshold: {row.get('Threshold', 'N/A')} {row.get('Unit', '')})"), width=6),
                dbc.Col(dcc.Input(id={'type': 'risk-input', 'index': row['Sub Risk Drivers']}, type='number', placeholder='Enter Status'), width=4),
                dbc.Col(html.Button('Analyze Risk', id={'type': 'analyze-risk', 'index': row['Sub Risk Drivers']}, n_clicks=0), width=2)
            ], className='mb-3')
            for _, row in group.iterrows()
        ]
        content.append(html.Div([
            html.H4(name, className='bg-primary text-white p-2'),
            html.Div(rows)
        ]))

    return html.Div(content)

def create_summary_tab(df):
    # Summary content based on your application's logic
    return html.Div([html.P(f"Summary info for {row['Sub Risk Drivers']}") for _, row in df.iterrows()])

@app.callback(
    Output('output-weights', 'children'),
    Input({'type': 'render-button', 'index': ALL}, 'n_clicks'),
    State('stored-data', 'data'),
    prevent_initial_call=True
)
def update_weights_output(n_clicks, data):
    ctx = dash.callback_context
    if not ctx.triggered or not data:
        return "No data to display."
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    risk_driver = json.loads(button_id)['index']
    df = pd.DataFrame(data)
    group = df[df['Risk Drivers'] == risk_driver]
    charts_dict = create_charts(group)
    return [
        dbc.Row([
            dbc.Col(dcc.Graph(figure=chart['bar_fig']), width=6),
            dbc.Col(dcc.Graph(figure=chart['pie_fig']), width=6)
        ]) for _, chart in charts_dict.items()
    ]



if __name__ == '__main__':
    app.run_server(debug=True)