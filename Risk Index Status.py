import dash
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from dash_bootstrap_components import Row
from dash.dependencies import ALL
import plotly.express as px
import pandas as pd
import io
import base64

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Function to parse contents of the uploaded file
def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    return pd.read_excel(io.BytesIO(decoded))

# Function to determine risk index
def determine_risk_index(status, threshold):
    range_under_threshold = threshold * 0.10  # Allowing 10% range under the threshold
    if status < threshold:
        return 1  # Low Risk
    elif threshold <= status <= (threshold + range_under_threshold):
        return 2  # Approaching Risk
    else:
        return 3  # At Risk

# Layout for the application
app.layout = html.Div([
    dcc.Tabs(id='tabs', value='tab-1', children=[
        dcc.Tab(label='Upload and Analyze', value='tab-1'),
    ]),
    html.Div(id='tabs-content')
])

# Callback to render content in tabs
@app.callback(Output('tabs-content', 'children'),
              Input('tabs', 'value'))
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            html.Div([
                dcc.Textarea(
                    id='instructions-textbox',
                    value='Please upload an Excel file with Risk Drivers, their Sub Risk Drivers, your projects risk thresholds and the units for those thresholds',
                    style={'width': '60%', 'height': '50px'},
                    readOnly=True
                ),
                html.Br(),
                dcc.Upload(
                    id='upload-data',
                    children=dbc.Button('Upload File', id='upload-button', className='mb-3'),
                    multiple=False,
                    style={'display': 'block'}
                ),
                html.Br(),
            ], style={'marginBottom': '20px'}),
            html.Div(id='status-input-form'),
            html.Button('Analyze Risk', id='analyze-button', n_clicks=0, style={'display': 'block', 'marginBottom': '20px'}),
            html.Div(id='graph-container')  # Container for the graph
        ])
    return html.Div("This tab is not yet implemented")  # Provide a default return for unimplemented tabs

# Callback to update the status input form based on the uploaded Excel sheet
@app.callback(
    Output('status-input-form', 'children'),
    Input('upload-data', 'contents'))
def update_status_input_form(contents):
    if contents is None:
        raise dash.exceptions.PreventUpdate

    df = parse_contents(contents)
    df.columns = [col.lower() for col in df.columns]

    if 'risk drivers' not in df.columns:
        return html.Div("The uploaded file does not contain the required column 'Risk Drivers'.")

    risk_driver_categories = df['risk drivers'].unique()
    children = []
    
    # Instructions text area
    children.append(dcc.Textarea(
        id='instructions-textbox',
        value='Please enter the status for each Sub Risk Driver.',
        style={'width': '60%', 'height': '50px', 'marginBottom': '20px'},
        readOnly=True
    ))

    for category in risk_driver_categories:
        category_df = df[df['risk drivers'].str.lower() == category.lower()]
        inputs_list = []
        for index, row in category_df.iterrows():
            sub_driver_div = html.Div([
                html.Div([
                    html.P(row['sub risk drivers'], style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id={'type': 'status-input', 'index': row['sub risk drivers']},
                        type='number',
                        placeholder='Enter Status',
                        style={'width': '100px', 'marginRight': '10px'}
                    ),
                    html.Div([
                        html.Span(f"Threshold: {row['threshold']} {row['unit']}")
                    ], style={'fontSize': 'smaller'})
                ], style={'border': '1px solid lightgrey', 'padding': '10px', 'marginRight': '20px', 'width': '500px'})
            ], style={'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '20px'})
            inputs_list.append(sub_driver_div)

        children.append(html.Div([
            html.H4(category, style={'fontWeight': 'bold', 'marginBottom': '10px'}),
            html.Div(inputs_list, style={'marginBottom': '20px'})
        ]))
        # Add horizontal line between categories
        if category != risk_driver_categories[-1]:  # Avoid adding a line after the last category
            children.append(html.Hr(style={'margin': '20px 0'}))

    return children

# Callback to analyze risk and update the bar chart
@app.callback(
    [Output('graph-container', 'children'), Output('risk-summary-container', 'children')],
    Input('analyze-button', 'n_clicks'),
    State('upload-data', 'contents'),
    State({'type': 'status-input', 'index': ALL}, 'value')
)
def analyze_risk(n_clicks, contents, status_values):
    if n_clicks == 0 or contents is None:
        return html.Div(), html.Div()

    df = parse_contents(contents)
    df['Status'] = status_values
    df['Risk Index'] = df.apply(lambda x: determine_risk_index(x['Status'], x['Threshold']), axis=1)

    # Sorting the DataFrame by 'Risk Index'
    df.sort_values('Risk Index', ascending=False, inplace=True)

    # Mapping of risk index to colors
    risk_colors = {1: 'green', 2: 'yellow', 3: 'red'}

    # Creating the figure
    fig = px.bar(
        df,
        x='Sub Risk Drivers',
        y='Risk Index',
        color='Risk Index',
        color_discrete_map=risk_colors
    )
    fig.update_layout(yaxis=dict(range=[0, 4]))

    # Preparing the summary
    summary = {
        1: 'The following sub risk drivers are in good standings with the project\'s requirements: ',
        2: 'The following sub risk drivers are within bounds but should be monitored: ',
        3: 'The following sub risk drivers offer the most risk: '
    }
    for risk_index in [3, 2, 1]:
        summary[risk_index] += ', '.join(df[df['Risk Index'] == risk_index]['Sub Risk Drivers'].tolist())

    summary_text = html.Div([
        html.P(summary[3]),
        html.P(summary[2]),
        html.P(summary[1])
    ])
    
    # Creating the summary text elements with formatting
    summary_elements = []
    for risk_index, title in zip([3, 2, 1], ["The following sub risk drivers offer the most risk", "The following sub risk drivers are within bounds but should be monitored", "The following sub risk drivers are in good standings with the project\'s requirements"]):
        drivers = ', '.join(df[df['Risk Index'] == risk_index]['Sub Risk Drivers'].tolist())
        if drivers:
            summary_elements.append(html.P(children=[html.Strong(title + ': '), drivers], style={'textAlign': 'center'}))
        else:
            summary_elements.append(html.P(children=[html.Strong(title + ': '), "None"], style={'textAlign': 'center'}))

    summary_box = html.Div(
        children=summary_elements,
        style={
            'border': '1px solid lightgrey',
            'height': '150px',
            'padding': '10px',
            'margin': '10px',
            'textAlign': 'center',
            'width': '80%',
            'marginLeft': 'auto',
            'marginRight': 'auto'
        }
    )

    return dcc.Graph(figure=fig), summary_box

# Layout of the application
app.layout = html.Div([
    dcc.Tabs(id='tabs', value='tab-1', children=[
        dcc.Tab(label='Upload and Analyze', value='tab-1'),
    ]),
    html.Div(id='tabs-content'),
    html.Div(id='risk-summary-container')  # Container for the risk summary
])

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)