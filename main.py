import dash
from dash import Dash, dcc, html, Input, Output, State, ALL, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px


# Import your modular functions
from utils import parse_contents
from weights_mitigations import create_charts, calculate_priority_vector
from risk_index_status import determine_risk_index, process_risk_index

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])


app.layout = html.Div([
    dcc.Store(id='stored-data'),  # Store for holding uploaded data
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

def calculate_cumulative_risk_index(df):
    df['risk_index'] = df.apply(lambda row: determine_risk_index(row['status'], row['threshold']), axis=1)
    weighted_risk_indices = {}

    for risk_driver, group in df.groupby('risk_drivers'):
        priority_vector = group['pv'].to_numpy()
        risk_indices = group['risk_index'].to_numpy()
        weighted_risk_index = np.dot(priority_vector, risk_indices)
        weighted_risk_indices[risk_driver] = weighted_risk_index

    return weighted_risk_indices


@app.callback(
    Output('stored-data', 'data'),
    Input('upload-data', 'contents')
)
def handle_upload(contents):
    if contents is not None:
        df = parse_contents(contents)
        print("Columns in uploaded data:", df.columns)  # This will log the column names
        return df.to_dict('records')
    return None

@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value'),
    State('stored-data', 'data')
)
def render_tab_content(tab, data):
    if data is None:
        return "Please upload data to proceed."
    
    df = pd.DataFrame(data)
    # Normalize the risk driver names to ensure consistent grouping

    print("Columns after operation XYZ:", df.columns)

    
    if 'risk_drivers' not in df.columns:
        return "Required column 'Risk Drivers' is missing in the uploaded data."

    if tab == 'tab-weights':
        slider_groups = []
        for risk_driver, group in df.groupby('risk_drivers'):  # Use the correct column name
            sliders = [
                html.Div([
                    dbc.Label(f"{row['sub_risk_drivers']}"),
                    dcc.Slider(
                        id={'type': 'dynamic-slider', 'index': f"{risk_driver}-{row['sub_risk_drivers']}"},
                        min=0, max=10, step=1, value=5,
                        marks={i: str(i) for i in range(11)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], style={'margin': '20px'})
                for _, row in group.iterrows()
            ]
            slider_groups.append(html.Div([
                html.H3(risk_driver, style={'paddingTop': '20px'}),
                html.Div(sliders)
            ]))

        return html.Div([
            html.Div(slider_groups),
            dbc.Button('Render Graphs', id='btn-render-weights', n_clicks=0, style={'marginTop': '20px'}),
            html.Div(id='output-weights')
        ])

    elif tab == 'tab-risk':
        if data is None:
            return html.Div("Please upload data to proceed.")
        
        df = pd.DataFrame(data)
        # Normalize column names just in case they aren't already
        df.columns = [x.replace(' ', '_').lower() for x in df.columns]

        if 'risk_drivers' not in df.columns or 'sub_risk_drivers' not in df.columns:
            return html.Div("The uploaded data does not contain the required columns 'Risk Drivers' and 'Sub Risk Drivers'.")

        # Create a dictionary to organize data by 'risk_drivers'
        risk_categories = df['risk_drivers'].unique()
        layout = html.Div([
            html.H3("Please enter the status for each Sub Risk Driver.", style={'margin': '20px'}),
            dbc.Row([
                dbc.Col([
                    html.Div(id=f'category-{cat}', children=[
                        html.H4(cat, className='mt-3 mb-2'),
                        dbc.Form([
                            dbc.Row([
                                dbc.Label(f"{row['sub_risk_drivers']} (Threshold: {row['threshold']} {row.get('unit', '')})", className="font-weight-bold", width=8),
                                dbc.Col(dbc.Input(type="number", placeholder="Enter Status"), width=4),
                            ], className='mb-3', align='center')
                            for index, row in df[df['risk_drivers'] == cat].iterrows()
                        ])
                    ]) 
                ], width=6) for cat in risk_categories
            ])
        ])
        return layout
    elif tab == 'tab-summary':
        if data is None:
            return html.Div("Please upload data to proceed.")
        
        df = pd.DataFrame(data)
        results = calculate_cumulative_risk_index(df)
        summary_content = [
            html.P("Summary of Weighted Risk Indices:"),
            html.Ul([html.Li(f"{driver}: {results[driver]}") for driver in results])
        ]
        return html.Div(summary_content)
    return html.Div("This tab is not yet implemented")



@app.callback(
    Output('output-weights', 'children'),
    Input('btn-render-weights', 'n_clicks'),
    State('stored-data', 'data'),
    State({'type': 'dynamic-slider', 'index': ALL}, 'value'),
    State({'type': 'dynamic-slider', 'index': ALL}, 'id')
)
def update_weights_output(n_clicks, data, slider_values, slider_ids):
    if n_clicks > 0 and data:
        df = pd.DataFrame(data)
        slider_values_dict = {slider['index']: value for slider, value in zip(slider_ids, slider_values)}
        charts_dict = create_charts(df, slider_values_dict)
        return [
            html.Div([
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=charts['bar_fig']), width=6),
                    dbc.Col(dcc.Graph(figure=charts['pie_fig']), width=6)
                ])
            ], style={'margin-bottom': '50px'}) for _, charts in charts_dict.items()
        ]
    return "No data to display."

@app.callback(
    Output('output-risk', 'children'),
    Input('btn-analyze-risk', 'n_clicks'),
    State('stored-data', 'data')
)
def update_risk_output(n_clicks, data):
    if n_clicks > 0 and data:
        df = pd.DataFrame(data)
        df['Risk Index'] = df.apply(lambda row: determine_risk_index(row['status'], row['threshold']), axis=1)
        return dcc.Graph(figure=px.bar(df, x='Sub Risk Drivers', y='Risk Index'))
    return "No data to display."

if __name__ == '__main__':
    app.run_server(debug=True)