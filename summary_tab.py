import dash
from dash import dcc, html, Input, Output, State, ALL, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import numpy as np
import pandas as pd
import base64
import io

from utils import parse_contents
from mitigation import mitigation_strategies

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout
app.layout = html.Div([
    dcc.Store(id='data-store'),
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload File', className='btn btn-primary'),
        style={'width': '100%', 'height': '50px', 'lineHeight': '50px'},
        multiple=True
    ),
    html.Div(id='file-list', style={'margin': '20px'}),
    html.Div(id='graphs-container'),
    html.Div(id='mitigation-container'),
    html.Div(id='summary-output')
])

@app.callback(
    Output('data-store', 'data'),
    Input('upload-data', 'contents'),
    prevent_initial_call=True
)
def process_data(contents):
    if contents:
        datasets = [pd.read_excel(io.BytesIO(base64.b64decode(c.split(',')[1]))).to_dict('records') for c in contents]
        return datasets
    return []

@app.callback(
    [Output('graphs-container', 'children'), Output('mitigation-container', 'children')],
    Input('data-store', 'data'),
    prevent_initial_call=True
)
def update_output(data):
    if data:
        figures = []
        dfs_with_risk = []  # List to hold DataFrames that have 'Weighted Risk'
        
        for d in data:
            df = pd.DataFrame(d)
            if 'Weight' in df.columns and 'Risk Index' in df.columns:
                df['Weighted Risk'] = df['Weight'] * df['Risk Index']
                fig = px.bar(df, x='Sub Risk Drivers', y='Weighted Risk', color='Risk Index', title="Risk Analysis per File")
                figures.append(dcc.Graph(figure=fig))
                dfs_with_risk.append(df)  # Add to list only if 'Weighted Risk' was calculated
            else:
                figures.append(html.Div("Required columns missing in uploaded file."))

        # Check if there are any DataFrames to concatenate
        if dfs_with_risk:
            df_all = pd.concat(dfs_with_risk)
            top_risks = df_all.sort_values(by='Weighted Risk', ascending=False).head(5)
            mitigation_elements = [html.H5("Mitigation Strategies")] + [
                html.Div([
                    html.H6(sub_driver),
                    html.Ul([html.Li(s) for s in mitigation_strategies.get(sub_driver, ["No specific mitigation strategy provided."])])
                ]) for sub_driver in top_risks['Sub Risk Drivers']
            ]
        else:
            mitigation_elements = [html.Div("No data with 'Weighted Risk' found to analyze mitigation strategies.")]

        return figures, html.Div(mitigation_elements)
    return html.Div("No file uploaded."), html.Div()




@app.callback(
    Output('file-list', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def update_file_list(list_of_contents, list_of_names):
    if list_of_contents:
        children = [
            html.Div([
                html.Button(filename, id={'type': 'file-button', 'index': i}, n_clicks=0, className='btn btn-link')
            ]) for i, filename in enumerate(list_of_names)
        ]
        return children
    return "No files uploaded."

def calculate_overall_risk_evaluation(dataframe):
    dataframe['Weighted Risk'] = dataframe['Weight'] * dataframe['Risk Index']
    overall_risk_scores = dataframe.groupby('Risk Drivers')['Weighted Risk'].sum()
    return overall_risk_scores

@app.callback(
    Output('summary-output', 'children'),
    Input({'type': 'file-button', 'index': ALL}, 'n_clicks'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def display_summary(n_clicks, list_of_contents, list_of_filenames):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "Select a file to view the summary."
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        file_index = eval(button_id)['index']
        content_type, content_string = list_of_contents[file_index].split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(io.BytesIO(decoded))
        overall_scores = calculate_overall_risk_evaluation(df)
        
        return html.Div([
            html.H5(f"Summary for {list_of_filenames[file_index]}"),
            dcc.Graph(
                figure={
                    'data': [{'x': overall_scores.index, 'y': overall_scores.values, 'type': 'bar'}],
                    'layout': {'title': 'Risk Evaluation Scores'}
                }
            )
        ])

if __name__ == '__main__':
    app.run_server(debug=True)
