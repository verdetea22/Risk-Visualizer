# utils.py
import pandas as pd
import io
import base64

def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_excel(io.BytesIO(decoded))
    # Normalize column names to lowercase with underscores, ensuring uniformity across your application
    df.columns = [x.strip().lower().replace(' ', '_').lower() for x in df.columns]
    return df
