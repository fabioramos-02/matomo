import pandas as pd
import warnings
warnings.filterwarnings('error')

path = "matomo-analytics-dashboard/exports/cartas_errors.csv"
try:
    df = pd.read_csv(
        path, 
        sep=';', 
        on_bad_lines='skip',
        encoding='utf-8-sig',
        low_memory=False
    )
    print("CSV loaded successfully.")
    for col in df.columns:
        if any(x in col for x in ["data_", "created_at", "updated_at"]):
            print(f"Converting column {col}...")
            df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
    print("Dates converted.")
except Exception as e:
    print(f"Exception: {e}")
