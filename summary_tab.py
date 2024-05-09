# summary_tab.py
from dash import html
import dash
from dash import dcc, html, Input, Output, State, ALL, callback
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc

def create_summary_report(weights_data, risk_index_data):
    # Example of creating a simple summary report
    summary = html.Div([
        html.H4('Summary Report'),
        html.P(f"Weights Data: {weights_data}"),
        html.P(f"Risk Index Data: {risk_index_data}")
    ])
    return summary

@callback(
    Output('summary-report', 'children'),
    [Input('weights-data', 'data'), Input('risk-index-data', 'data')]
)
def update_summary_report(weights_data, risk_index_data):
    if weights_data and risk_index_data:
        return create_summary_report(weights_data, risk_index_data)
    return "Data is missing, please complete all sections."

# summary_tab.py
def summary_tab_layout():
    return html.Div([
            dcc.Input(id='session-name', type='text', placeholder='Enter a name for this session'),
            html.Button('Save Session', id='save-session-button'),
            html.Div(id='save-status'),
            html.Div(id='summary-report')
    ])

# summary_tab.py
def save_data_to_server_or_local(session_name, weights_data, risk_index_data):
    # Example: Mock saving to server/local
    print(f"Saving session {session_name} with weights data {weights_data} and risk index data {risk_index_data}")
    # Implement actual save logic here depending on your backend.
    return True

@callback(
    Output('save-status', 'children'),
    Input('save-session-button', 'n_clicks'),
    State('session-name', 'value'),
    State('weights-data', 'data'),
    State('risk-index-data', 'data')
)
def save_session(n_clicks, session_name, weights_data, risk_index_data):
    if n_clicks:
        if save_data_to_server_or_local(session_name, weights_data, risk_index_data):
            return 'Session saved successfully!'
        else:
            return 'Failed to save session.'
    return ''
