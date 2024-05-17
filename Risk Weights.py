import dash
from dash import Dash, dcc, html, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import plotly.express as px
import numpy as np
import pandas as pd
import io
import base64
import json
import plotly.graph_objs as go

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

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

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload File', id='upload-button', style={'width': '100%', 'height': '50px', 'lineHeight': '50px'}),
        multiple=False,
        style={'textAlign': 'center', 'padding': '20px'}
    ), 
    
    html.Div( 
        'Rank the following sub-risk drivers in terms of their importance to your project, relative to one another:',
        style={
            'textAlign': 'center',
            'margin': '10px',
            'padding': '10px',
            'backgroundColor': '#f7f7f7',
            'borderRadius': '5px',
            'border': '1px solid #d6d6d6',
            'color': '#333'
        }
    ),html.Div(id='sliders-container', style=CONTENT_STYLE),
    html.Button('Render', id='render-button', style={'width': '100%', 'height': '50px', 'lineHeight': '50px', 'background-color': '#007BFF', 'color': 'white', 'border': 'none'}),
    html.Div(id='log', style={'whiteSpace': 'pre-line', 'margin': '10px',}),
    html.Div(id='graphs-container', style=CONTENT_STYLE),
    
], style={'max-width': '1800px', 'margin': '0 auto'})


@app.callback(
    Output('sliders-container', 'children'),
    [Input('upload-data', 'contents')]
)
def update_sliders(contents):
    if contents:
        df = parse_contents(contents)
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
                    value=1,
                    marks={i: str(i) for i in range(10)}
                )
            ]) for sub_driver in sub_drivers]
            sliders.append(html.Div([
                html.H3(driver),
                html.Div(sliders_for_driver, style={'border': 'thin lightgrey solid', 'padding': '20px'})
            ]))
        return sliders
    return 'Please upload an Excel file'

@app.callback(
    Output('graphs-container', 'children'),
    [Input('render-button', 'n_clicks')],
    [State('upload-data', 'contents'),
     State({'type': 'dynamic-slider', 'index': ALL}, 'value'),
     State({'type': 'dynamic-slider', 'index': ALL}, 'id')]
)

def render_graphics(n_clicks, contents, slider_values, slider_ids):
    if n_clicks and contents:
        df = parse_contents(contents)
        slider_values_dict = {slider['index']: value for slider, value in zip(slider_ids, slider_values)}
        
        # Create charts for each risk driver as per the order in the dataframe
        charts_dict = create_charts(df, slider_values_dict)
        
        # Initialize a list to hold the Divs for summaries and graphs
        divs = []

        # Iterate through the charts_dict in the order of risk drivers
        for risk_driver in df['Risk Drivers'].unique():
            charts = charts_dict[risk_driver]
            pie_data = charts['pie_fig'].data[0]
            max_value_index = np.argmax(pie_data['values'])
            most_important_sub_driver = pie_data['labels'][max_value_index]
            mitigation_strategy = mitigation_strategies.get(most_important_sub_driver, [html.P('No specific mitigation strategy provided.')])

            # Create the summary card for the current risk driver
            summary_card = dbc.Card(
                dbc.CardBody([
                    html.H4(f'Most important area for {risk_driver}:', style=CARD_TEXT_STYLE),
                    html.P(f"{most_important_sub_driver} (PV: {pie_data['values'][max_value_index]:.2f})", style=CARD_TEXT_STYLE),
                    html.H4('Suggested Mitigation Strategy:', style=CARD_TEXT_STYLE),
                    *mitigation_strategy
                ]),
                style=CARD_STYLE
            )

            # Create the graph row for the current risk driver
            graph_row = dbc.Row([
                dbc.Col(dcc.Graph(figure=charts['bar_fig']), md=6),
                dbc.Col(dcc.Graph(figure=charts['pie_fig']), md=6)
            ], className='mb-4')

            # Append the summary card and graph row to the divs list
            divs.append(html.Div([
                html.H3(f'{risk_driver} Summary', style=TEXT_STYLE),
                summary_card,
                html.H3(f'{risk_driver} Graphics', style=TEXT_STYLE),
                graph_row
            ], style={'margin-bottom': '50px'}))

        return divs

    return html.Div('No data to display, please upload a file and render the graphs.')

mitigation_strategies = {
    # Process
    'IT System Failures': [
        html.P("Establish a comprehensive IT disaster recovery plan and conduct regular system backups."),
        html.P("Implement redundant systems and high-availability solutions to minimize downtime."),
    ],
    'Technological Obsolescence': [
        html.P("Schedule regular technology reviews and establish a replacement cycle aligned with industry standards."),
        html.P("Invest in employee training on new technologies and foster a culture of continuous learning."),
    ],
    'Supplier Count Range': [
        html.P("Conduct periodic reviews of supplier performance and diversify supplier base to mitigate risks."),
        html.P("Develop strategic partnerships with key suppliers to ensure reliable supply chains."),
    ],

    # Organization Structure
    'Labor Strikes': [
        html.P("Foster a work environment that values employee feedback and promotes fair labor practices."),
        html.P("Establish contingency plans to maintain operations during periods of labor unrest."),
    ],
    'Cost Overruns': [
        html.P("Implement stringent budget controls and regular audit mechanisms."),
        html.P("Adopt project management methodologies that emphasize cost control."),
    ],

    # Environment
    'Environmental Regulations': [
        html.P("Stay updated with regulatory changes and ensure compliance through regular audits."),
        html.P("Invest in sustainable practices and technologies that exceed regulatory requirements."),
    ],
    'Natural Disasters': [
        html.P("Develop and regularly update an emergency preparedness and response plan."),
        html.P("Invest in insurance and infrastructure that can withstand environmental risks."),
    ],
    'Regulatory Changes': [
        html.P("Engage with policymakers and industry associations to stay ahead of potential regulatory changes."),
        html.P("Adopt flexible business strategies that can quickly adapt to new regulations."),
    ],
    'Global Pandemic': [
        html.P("Create a pandemic response plan that includes remote working capabilities and health protocols."),
        html.P("Maintain a reserve of essential supplies and diversify production locations to minimize disruptions."),
    ],
    'Market Demand Fluctuations': [
        html.P("Use predictive analytics to understand market trends and adjust production accordingly."),
        html.P("Diversify product offerings to cater to different market segments and reduce reliance on a single product."),
    ],
    'Currency Fluctuations': [
        html.P("Use financial hedging instruments to manage risks related to currency exchange rates."),
        html.P("Diversify revenue streams across different currencies to mitigate potential losses."),
    ],

    # Upstream
    'Political Instability': [
        html.P("Monitor political developments and have contingency plans for rapid response."),
        html.P("Diversify operations across regions to mitigate the impact of political instability in any one area."),
    ],
    'Supplier Delays': [
        html.P("Implement just-in-time inventory systems and establish backup suppliers."),
        html.P("Strengthen supplier relationships and contracts to include delivery guarantees."),
    ],
    'Supply Chain Disruptions': [
        html.P("Develop a resilient supply chain with multiple logistics options."),
        html.P("Invest in supply chain visibility tools for real-time tracking of goods."),
    ],
    'Supplier Financial Instability': [
        html.P("Perform regular financial assessments of suppliers and develop risk profiles."),
        html.P("Secure alternative suppliers for critical components to reduce dependency."),
    ],

    # Downstream
    'Baggage Handling System Failure': [
        html.P("Conduct regular maintenance and simulations to ensure baggage system reliability."),
        html.P("Invest in technology upgrades and staff training for efficient baggage handling operations."),
    ],
}





def update_summary(n_clicks, contents, slider_values, slider_ids):
    if n_clicks and contents:
        df = parse_contents(contents)
        slider_values_dict = {slider['index']: value for slider, value in zip(slider_ids, slider_values)}
        charts_dict = create_charts(df, slider_values_dict)
        summary = []
        for risk_driver, charts in charts_dict.items():
            pie_data = charts['pie_fig'].data[0]
            max_value_index = np.argmax(pie_data['values'])
            most_important_sub_driver = pie_data['labels'][max_value_index]
            mitigation_strategy = mitigation_strategies.get(most_important_sub_driver, 'No specific mitigation strategy provided.')

            summary.append(html.Div([
    dbc.Card([
        dbc.CardBody([
            html.H4(f'Most important area for {risk_driver}:', style=CARD_TEXT_STYLE),
            html.P(f"{most_important_sub_driver} (PV: {pie_data['values'][max_value_index]:.2f})", style=CARD_TEXT_STYLE),
            html.H4('Suggested Mitigation Strategy:'),
                *mitigation_strategy
        ])
    ], style=CARD_STYLE)
], style={'margin-bottom': '20px'}))
        return summary
    return html.Div('Click "Render" to generate summary and mitigation strategies.')



if __name__ == '__main__':
    app.run_server(debug=True)
