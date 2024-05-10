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
    dcc.Store(id='data-store'),  # Store uploaded data
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload File', className='btn btn-primary'),
        style={'width': '100%', 'height': '50px', 'lineHeight': '50px'},
        multiple=True
    ),
    html.Div(id='file-list', style={'margin': '20px'}),  # Placeholder for file list
    html.Div(id='graphs-container'),
    html.Div(id='mitigation-container'),
    html.Div(id='summary-output')  # Ensure this is in the initial layout
])


@app.callback(
    Output('data-store', 'data'),
    Input('upload-data', 'contents'),
    prevent_initial_call=True
)
def process_data(contents):
    if contents:
        datasets = []
        for content in contents:
            content_type, content_string = content.split(',')
            decoded = base64.b64decode(content_string)
            df = pd.read_excel(io.BytesIO(decoded))
            datasets.append(df.to_dict('records'))
        return datasets
    return []

@app.callback(
    [Output('graphs-container', 'children'),
     Output('mitigation-container', 'children')],
    Input('data-store', 'data'),
    prevent_initial_call=True
)
def update_output(data):
    if data:
        df = pd.concat([pd.DataFrame(d) for d in data])
        df['Weighted Risk'] = df['Weight'] * df['Risk Index']
        # Plotting the risks for all sub risk drivers
        fig = px.bar(df, x='Sub Risk Drivers', y='Weighted Risk', color='Risk Index')

        # Generating mitigation strategies for top risk sub drivers
        top_risks = df.sort_values(by='Weighted Risk', ascending=False).head(5)
        mitigation_elements = [html.H5("Mitigation Strategies")]
        for sub_driver in top_risks['Sub Risk Drivers']:
            strategies = mitigation_strategies.get(sub_driver, ["No specific mitigation strategy provided."])
            mitigation_elements.append(html.Div([
                html.H6(sub_driver),
                html.Ul([html.Li(s) for s in strategies])
            ]))

        return dcc.Graph(figure=fig), html.Div(mitigation_elements)
    return html.Div("No file uploaded."), html.Div()

# Callback to list files
@app.callback(
    Output('file-list', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    prevent_initial_call=True
)
def update_file_list(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            html.Div([
                html.Button(filename, id={'type': 'file-button', 'index': i}, n_clicks=0, className='btn btn-link')
            ]) for i, filename in enumerate(list_of_names)
        ]
        return children
    return "No files uploaded."


def calculate_overall_risk_evaluation(dataframe):
    # Calculate the weighted risk for each sub risk driver
    dataframe['Weighted Risk'] = dataframe['Weight'] * dataframe['Risk Index']
    
    # Aggregate the weighted risks for each risk driver category
    overall_risk_scores = dataframe.groupby('Risk Drivers')['Weighted Risk'].sum()
    
    return overall_risk_scores

# Callback to handle file selection and process data
@app.callback(
    Output('summary-output', 'children',allow_duplicate=True),
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
        
        # Process data
        overall_scores = calculate_overall_risk_evaluation(df)  # Assuming this function is defined
        
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
