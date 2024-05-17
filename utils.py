# utils.py
import pandas as pd
import io
import base64

def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_excel(io.BytesIO(decoded))

    # Normalize column names to ensure consistency
    df.columns = df.columns.str.strip()  # Strip any leading/trailing whitespace
    df.columns = df.columns.str.replace('_', ' ')  # Replace spaces with underscores
    df.columns = df.columns.str.title()  # Ensure title case for uniformity

    print("Parsed DataFrame columns:", df.columns)
    return df
