import numpy as np

def determine_risk_index(status, threshold):
    range_under_threshold = threshold * 0.10  # Allowing 10% range under the threshold
    if status < threshold:
        return 1  # Low Risk
    elif threshold <= status <= (threshold + range_under_threshold):
        return 2  # Approaching Risk
    else:
        return 3  # High Risk
    
def process_risk_index(data):
    # Add your detailed implementation based on the project specifics
    return data

def calculate_cumulative_risk_index(df):
    df['risk_index'] = df.apply(lambda row: determine_risk_index(row['status'], row['threshold']), axis=1)
    weighted_risk_indices = {}
    print(df.columns)

    for risk_driver, group in df.groupby('Risk_Drivers'):
        priority_vector = group['pv'].to_numpy()
        risk_indices = group['risk_index'].to_numpy()
        weighted_risk_index = np.dot(priority_vector, risk_indices)
        weighted_risk_indices[risk_driver] = weighted_risk_index

    return weighted_risk_indices