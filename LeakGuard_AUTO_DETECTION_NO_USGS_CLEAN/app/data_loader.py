
import pandas as pd
import numpy as np

def read_uploaded_csv(uploaded):
    df = pd.read_csv(uploaded)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def infer_columns(df):
    cols = {c.lower(): c for c in df.columns}
    pressure = [c for c in df.columns if any(k in c.lower() for k in ["pressure","press","head"])]
    flow = [c for c in df.columns if any(k in c.lower() for k in ["flow","demand","discharge"])]
    time = [c for c in df.columns if any(k in c.lower() for k in ["time","date","timestamp"])]
    return {
        "pressure": pressure,
        "flow": flow,
        "time": time,
    }

def research_summary(df):
    inferred = infer_columns(df)
    result = {
        "rows": len(df),
        "columns": len(df.columns),
        "pressure_columns": inferred["pressure"],
        "flow_columns": inferred["flow"],
        "time_columns": inferred["time"],
    }
    numeric = df.select_dtypes(include=np.number)
    result["numeric_columns"] = list(numeric.columns)
    return result
