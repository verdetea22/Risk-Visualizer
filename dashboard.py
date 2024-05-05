import dash
from dash import Dash, dcc, html, Input, Output, State, ALL, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import io
import base64

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Function to parse contents of the uploaded file
def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    return pd.read_excel(io.BytesIO(decoded))

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

# Main layout of the application
app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload File', style={'width': '100%', 'height': '50px'}),
        style={'textAlign': 'center', 'padding': '20px'},
        multiple=False
    ),
    dcc.Tabs(id='tabs', children=[
        dcc.Tab(label='Weights and Mitigations', value='tab-weights'),
        dcc.Tab(label='Risk Index', value='tab-risk'),
    ]),
    html.Div(id='tabs-content')
])

# Callback for rendering tab content
@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value'),
    State('upload-data', 'contents')
)
def render_tab_content(tab, contents):
    if contents is None:
        return "Please upload data to proceed."

    df = parse_contents(contents)

    if tab == 'tab-weights':
        return html.Div([
            dbc.Button('Render Graphs', id='btn-render-weights', n_clicks=0),
            html.Div(id='output-weights')
        ])
    elif tab == 'tab-risk':
        return html.Div([
            dbc.Button('Analyze Risk', id='btn-analyze-risk', n_clicks=0),
            html.Div(id='output-risk')
        ])
    return "Tab not implemented."

# Callbacks for each specific functionality
@app.callback(
    Output('output-weights', 'children'),
    Input('btn-render-weights', 'n_clicks'),
    State('upload-data', 'contents')
)
def update_weights_output(n_clicks, contents):
    if n_clicks > 0 and contents:
        df = parse_contents(contents)
        slider_values_dict = {}  # This should be replaced with actual logic to gather slider values
        charts_dict = create_charts(df, slider_values_dict)
        return [dcc.Graph(figure=chart['bar_fig']) for _, chart in charts_dict.items()]
    return "No data to display."

@app.callback(
    Output('output-risk', 'children'),
    Input('btn-analyze-risk', 'n_clicks'),
    State('upload-data', 'contents')
)
def update_risk_output(n_clicks, contents):
    if n_clicks > 0 and contents:
        df = parse_contents(contents)
        # Implement your risk analysis logic here
        return html.Div("Risk analysis output goes here.")
    return "No data to display."

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)
