import dash
from dash import dcc, html, Input, Output, State, ALL, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
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
            html.Div(id='summary-chart-container', style={'padding': '20px', 'backgroundColor': '#f9f9f9', 'border': '1px solid #ccc', 'borderRadius': '5px', 'margin': '10px 0'}),
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
        datasets = []
        for content in contents:
            df = parse_contents(content)
            datasets.append(df.to_dict('records'))
        return {'data': datasets, 'filenames': filenames}
    return {}


@app.callback(
    Output('graphs-container', 'children'),
    Input('data-store', 'data'),
    prevent_initial_call=True
)
def update_individual_assessments(stored_data):
    print("Callback triggered with stored_data keys:", stored_data.keys())  # Debug print

    if stored_data and 'data' in stored_data and 'filenames' in stored_data:
        data = stored_data['data']
        filenames = stored_data['filenames']
        combined_df = pd.DataFrame()

        for df_data, filename in zip(data, filenames):
            df = pd.DataFrame(df_data)
            df['Stakeholder'] = filename
            combined_df = pd.concat([combined_df, df])

        print("Combined DataFrame head:\n", combined_df.head())  # Debug print

        # Check if required columns are present
        if {'Weight', 'Risk Index', 'Sub Risk Drivers', 'Stakeholder'}.issubset(combined_df.columns):
            # Scatterplot for combined data
            scatter_fig = px.scatter(combined_df, 
                                     x='Sub Risk Drivers', 
                                     y='Risk Index', 
                                     color='Stakeholder', 
                                     size='Weight', 
                                     title="Combined Risk Assessment Scatterplot")
            return [html.Div([
                html.P("Combined Scatterplot:"),
                html.Hr(),
                dcc.Graph(figure=scatter_fig),
                html.Hr()
            ])]
        else:
            print("Required columns are missing in the combined DataFrame")  # Debug print

    return [html.Div("No data available for scatter plot.")]


@app.callback(
    [Output('summary-chart-container', 'children'),
     Output('master-chart-container', 'children'),
     Output('mitigation-container', 'children')],
    Input('data-store', 'data'),
    prevent_initial_call=True
)
def update_master_chart(stored_data):
    print("Callback triggered with stored_data keys:", stored_data.keys())  # Debug print

    if stored_data and 'data' in stored_data and 'filenames' in stored_data:
        data = stored_data['data']
        filenames = stored_data['filenames']
        dfs_with_risk = []

        for df_data, filename in zip(data, filenames):
            df = pd.DataFrame(df_data)
            print(f"Processing file: {filename}")  # Debug print
            print("DataFrame head:\n", df.head())  # Debug print

            # Check if required columns are present
            if {'Weight', 'Risk Index', 'Stakeholder', 'Sub Risk Drivers'}.issubset(df.columns):
                # Prepare data for the master chart
                dfs_with_risk.append(df)
            else:
                print(f"Required columns are missing in file: {filename}")  # Debug print

        # Ensure dfs_with_risk is not empty before processing master chart
        if dfs_with_risk:
            df_all = pd.concat(dfs_with_risk)
            df_all.sort_values('Weight', ascending=False, inplace=True)  # Sort by 'Weight' in descending order
            print("Combined DataFrame head:\n", df_all.head())  # Debug print
            
            # Create the master chart with mean and standard deviation
            if not df_all.empty:
                df_grouped = df_all.groupby('Sub Risk Drivers')['Weight'].agg(['mean', 'std']).reset_index()
                df_grouped.columns = ['Sub Risk Drivers', 'Mean Weighted Risk', 'Standard Deviation']
                
                # Sort the grouped DataFrame by mean weighted risk
                df_grouped.sort_values('Mean Weighted Risk', ascending=False, inplace=True)
                print("Grouped DataFrame head:\n", df_grouped.head())  # Debug print
                
                master_fig = go.Figure()
                master_fig.add_trace(go.Bar(
                    x=df_grouped['Sub Risk Drivers'],
                    y=df_grouped['Mean Weighted Risk'],
                    name='Mean Weighted Risk',
                    marker_color='blue'
                ))
                
                # Add error bars for standard deviation
                master_fig.add_trace(go.Bar(
                    x=df_grouped['Sub Risk Drivers'],
                    y=df_grouped['Standard Deviation'],
                    name='Standard Deviation',
                    marker_color='orange'
                ))
                
                master_fig.update_layout(
                    title="Master Risk Analysis",
                    barmode='group',
                    xaxis_title="Sub Risk Drivers",
                    yaxis_title="Values",
                    legend_title="Metrics"
                )
                
                master_chart = dcc.Graph(figure=master_fig)

                # Summary statistics
                top_5_risks = df_grouped.nlargest(5, 'Mean Weighted Risk')
                top_5_std = df_grouped.nlargest(5, 'Standard Deviation')
                overall_std = df_grouped['Standard Deviation'].mean() * 100  # Convert to percentage
                
                if overall_std <= 10:
                    std_comment = "Standard Deviation is Allowable and Understandable"
                elif 10 < overall_std <= 30:
                    std_comment = "Standard Deviation is Medium"
                else:
                    std_comment = "Standard Deviation is Higher than Average"

                summary_chart = html.Div([
                    html.H5("Summary Statistics:"),
                    html.P(f"Top 5 Sub Risk Categories with Greatest Risk: {', '.join(top_5_risks['Sub Risk Drivers'])}"),
                    html.P(f"Top 5 Sub Risk Categories with Greatest Standard Deviation: {', '.join(top_5_std['Sub Risk Drivers'])}"),
                    html.P(f"Overall Standard Deviation: {overall_std:.2f}%, {std_comment}")
                ], style={'padding': '20px', 'backgroundColor': '#f9f9f9', 'border': '1px solid #ccc', 'borderRadius': '5px', 'margin': '10px 0'})
                
                master_top_risks = df_all.nlargest(5, 'Weight')
                master_mitigation = [html.H5("Mitigation Strategies for Master Chart")]
                master_mitigation.extend([
                    html.Div([
                        html.H6(risk['Sub Risk Drivers']),
                        html.Ul([html.Li(s) for s in mitigation_strategies.get(risk['Sub Risk Drivers'], ["No specific mitigation strategy provided."])])
                    ], style=mitigation_box_style) for _, risk in master_top_risks.iterrows()
                ])
            else:
                master_chart = html.Div("No data available for Master Chart.")
                summary_chart = html.Div("No data available for Summary Chart.")
                master_mitigation = [html.Div("No data with 'Weighted Risk' found to analyze mitigation strategies.")]
        else:
            master_chart = html.Div("No data available for Master Chart.")
            summary_chart = html.Div("No data available for Summary Chart.")
            master_mitigation = [html.Div("No data with 'Weighted Risk' found to analyze mitigation strategies.")]

        return summary_chart, master_chart, html.Div(master_mitigation)
    return html.Div("No file uploaded."), html.Div(), html.Div()




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
