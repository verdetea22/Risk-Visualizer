#weights_tab.py
import dash
from dash import dcc, html, Input, Output, State, ALL, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import numpy as np
import pandas as pd
from utils import parse_contents
from mitigation import mitigation_strategies



def risk_index_tab_layout():
    return html.Div([
        html.Div([
            dcc.Input(id='session-name', type='text', placeholder='Enter a name for this session'),
            html.Button('Save Session', id='save-session-button'),
            html.Div(id='save-status')
        ]),
        html.Div(id='summary-report')
    ])