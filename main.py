import dash
from dash import dcc, html, Dash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from weights_tab import weights_tab_layout, render_graphics

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dcc.Store(id='app-data'),  # Central storage for app data
    dcc.Tabs(id='app-tabs', children=[
        dcc.Tab(label='Weights', value='weights-tab'),
        dcc.Tab(label='Risk Index', value='risk-index-tab'),
        dcc.Tab(label='Summary & Mitigation', value='summary-tab'),
    ], value='weights-tab'),
    html.Div(id='tab-content')
])

@app.callback(
    Output('tab-content', 'children'),
    Input('app-tabs', 'value')
)
def render_tab(tab):
    if tab == 'weights-tab':
        return weights_tab_layout()
    elif tab == 'risk-index-tab':
        return html.Div("Risk Index Tab Content")
    elif tab == 'summary-tab':
        return html.Div("Summary & Mitigation Tab Content")
    return html.Div("Select a tab")

if __name__ == '__main__':
    app.run_server(debug=True)
