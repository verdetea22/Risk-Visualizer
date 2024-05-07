# utils.py
import pandas as pd
import io
import base64

def parse_contents(contents):
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(io.BytesIO(decoded))

        # Normalize column names
        df.columns = df.columns.str.strip().str.replace(' ', '').str.title()  # Example: " RiskDrivers " -> "Riskdrivers"
        print("Parsed DataFrame columns:", df.columns)
        return df
    except Exception as e:
        print("Error parsing file:", e)
        return pd.DataFrame()

