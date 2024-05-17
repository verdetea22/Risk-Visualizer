# weights_mitigations.py
import numpy as np
import plotly.express as px
import pandas as pd

def calculate_priority_vector(matrix):
    eigvals, eigvecs = np.linalg.eig(matrix)
    max_index = eigvals.argmax()
    priority_vector = np.abs(eigvecs[:, max_index])
    priority_vector /= priority_vector.sum()
    return priority_vector

def create_charts(df, slider_values_dict):
    charts_dict = {}
    for risk_driver, group_df in df.groupby('risk_drivers'):
        sliders = [slider_values_dict.get(f"{risk_driver}-{x}", 1) for x in group_df['sub_risk_drivers']]
        matrix = np.array([[sliders[i]/sliders[j] for j in range(len(sliders))] for i in range(len(sliders))])
        pv = calculate_priority_vector(matrix)

        bar_data = pd.DataFrame({
            'Sub Risk Drivers': group_df['sub_risk_drivers'],
            'Risk Index': pv
        })
        bar_fig = px.bar(bar_data, x='sub_risk_drivers', y='Risk Index', title=f'Risk Index - {risk_driver}')
        bar_fig.update_layout(yaxis=dict(range=[0, 1]))

        pie_data = pd.DataFrame({
            'Sub Risk Drivers': group_df['sub_risk_drivers'],
            'PV': pv
        })
        pie_fig = px.pie(pie_data, values='PV', names='sub_risk_drivers', title=f'Priority Vector - {risk_driver}')

        charts_dict[risk_driver] = {'bar_fig': bar_fig, 'pie_fig': pie_fig}
    return charts_dict



