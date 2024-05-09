import dash
from dash import dcc, html, Dash
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc

from weights_tab import weights_tab_layout, update_sliders, render_graphics
from risk_index_tab import risk_index_tab_layout  # Assuming similar structure for risk index
from summary_tab import summary_tab_layout


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)


app.layout = html.Div([
    dcc.Store(id='weights-data', storage_type='local'),  # Using local storage to persist data
    dcc.Store(id='risk-index-data', storage_type='local'),
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

@app.callback(
    Output('sliders-container', 'children'),
    Input('upload-data', 'contents')
)
def trigger_update_sliders(contents):
    return update_sliders(contents)

@app.callback(
    Output('graphs-container', 'children'),
    Input('render-button', 'n_clicks'),
    State('upload-data', 'contents'),
    State({'type': 'dynamic-slider', 'index': ALL}, 'value'),
    State({'type': 'dynamic-slider', 'index': ALL}, 'id')
)
def trigger_render_graphics(n_clicks, contents, slider_values, slider_ids):
    return render_graphics(n_clicks, contents, slider_values, slider_ids)




if __name__ == '__main__':
    app.run_server(debug=True)
