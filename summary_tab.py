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

# Define CSS styles
mitigation_box_style = {
    'border': '1px solid #ccc',
    'border-radius': '5px',
    'padding': '10px',
    'margin': '10px 0',
    'background-color': '#f9f9f9'
}

# Layout
app.layout = html.Div([
    dcc.Store(id='data-store'),
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload Files', className='btn btn-primary'),
        style={'width': '100%', 'height': '50px', 'lineHeight': '50px'},
        multiple=True
    ),
    dbc.Card(id='file-list', style={'margin': '20px', 'padding': '10px'}),
    dcc.Tabs(id='tabs', children=[
        dcc.Tab(label='Individual Assessments', children=[
            html.P("Individual Assessments:"),
            html.Hr(),
            html.Div(id='graphs-container')
        ]),
        dcc.Tab(label='Master Chart', children=[
            html.P("Master Chart:"),
            html.Hr(),
            html.Div(id='master-chart-container')
        ]),
    ]),
    html.Div(id='mitigation-container'),
    html.Div(id='summary-output')  # This is the new element where summaries will be displayed
])


@app.callback(
    Output('data-store', 'data'),
    [Input('upload-data', 'contents'),
     State('upload-data', 'filename')],
    prevent_initial_call=True
)
def process_data(contents, filenames):
    if contents:
        datasets = [pd.read_excel(io.BytesIO(base64.b64decode(c.split(',')[1]))).to_dict('records') for c in contents]
        return {'data': datasets, 'filenames': filenames}
    return {}


@app.callback(
    [Output('graphs-container', 'children'),
     Output('master-chart-container', 'children'),
     Output('mitigation-container', 'children')],
    Input('data-store', 'data'),
    prevent_initial_call=True
)
def update_output(stored_data):
    if stored_data and 'data' in stored_data and 'filenames' in stored_data:
        data = stored_data['data']
        filenames = stored_data['filenames']
        figures = []
        dfs_with_risk = []

        for df_data, filename in zip(data, filenames):
            df = pd.DataFrame(df_data)
            if 'Weight' in df.columns and 'Risk Index' in df.columns:
                df['Weighted Risk'] = df['Weight'] * df['Risk Index']
                df.sort_values('Weighted Risk', ascending=False, inplace=True)  # Sort by 'Weighted Risk' in descending order
                fig = px.bar(df, x='Sub Risk Drivers', y='Weighted Risk', color='Risk Index', title=f"Risk Analysis for {filename}")
                figures.append(html.Div([
                    html.P(f"Assessment and Mitigation Plan for {filename}:"),
                    html.Hr(),
                    dcc.Graph(figure=fig),
                    html.Hr()  # Divider after each file's assessment and mitigation plan
                ]))
                
                # Calculate top 5 risks and mitigation for each file
                top_risks = df.nlargest(5, 'Weighted Risk')
                mitigation = [html.H5(f"Mitigation Strategies for {filename}")]
                mitigation.extend([
                    html.Div([
                        html.H6(risk['Sub Risk Drivers']),
                        html.Ul([html.Li(s) for s in mitigation_strategies.get(risk['Sub Risk Drivers'], ["No specific mitigation strategy provided."])])
                    ], style=mitigation_box_style) for _, risk in top_risks.iterrows()
                ])
                figures.append(html.Div(mitigation))
                dfs_with_risk.append(df)

        # Master chart and mitigation strategies
        if dfs_with_risk:
            df_all = pd.concat(dfs_with_risk)
            df_all.sort_values('Weighted Risk', ascending=False, inplace=True)  # Sort by 'Weighted Risk' in descending order
            
            # Create the master chart
            master_fig = px.bar(df_all.groupby('Sub Risk Drivers')['Weighted Risk'].mean().reset_index(), x='Sub Risk Drivers', y='Weighted Risk', title="Master Risk Analysis")
            
            # Sort bars in descending order
            master_fig.update_traces(marker_color='green')  # Default color
            master_fig.update_traces(marker_color='yellow', selector=dict(type='bar', marker=dict(color='yellow')), row=0, col=0)
            master_fig.update_traces(marker_color='red', selector=dict(type='bar', marker=dict(color='red')), row=0, col=0)

            # Color top 5 red, next 5 yellow, and rest green
            master_chart = dcc.Graph(figure=master_fig)
            
            master_top_risks = df_all.nlargest(5, 'Weighted Risk')
            master_mitigation = [html.H5("Mitigation Strategies for Master Chart")]
            master_mitigation.extend([
                html.Div([
                    html.H6(risk['Sub Risk Drivers']),
                    html.Ul([html.Li(s) for s in mitigation_strategies.get(risk['Sub Risk Drivers'], ["No specific mitigation strategy provided."])])
                ], style=mitigation_box_style) for _, risk in master_top_risks.iterrows()
            ])
        else:
            master_chart = html.Div("No data available for Master Chart.")
            master_mitigation = [html.Div("No data with 'Weighted Risk' found to analyze mitigation strategies.")]

        return figures, master_chart, html.Div(master_mitigation)
    return [], html.Div("No file uploaded."), html.Div()


@app.callback(
    Output('file-list', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def update_file_list(list_of_contents, list_of_names):
    if list_of_contents:
        file_items = [html.Li(filename) for filename in list_of_names]
        return dbc.Card(dbc.CardBody([html.H4("Uploaded Files"), html.Ul(file_items)]), color="light", outline=True)
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
           html.Br(),
            html.H5(f"Summary for {list_of_filenames[file_index]}"),
            dcc.Graph(
                figure={
                    'data': [{'x': overall_scores.index, 'y': overall_scores.values, 'type': 'bar'}],
                    'layout': {'title': 'Risk Evaluation Scores'}
                }
            ),
            html.Br()
        ])


if __name__ == '__main__':
    app.run_server(debug=True)
