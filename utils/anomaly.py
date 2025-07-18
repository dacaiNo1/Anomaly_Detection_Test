import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

def run_anomaly_detection(df, n_estimators, contamination, max_samples, random_state):
    # Assume first column is an index-like column to ignore
    df = df.iloc[:, 1:]

    # Group-by candidates are columns before the first numeric column
    first_numeric_idx = df.select_dtypes(include=np.number).columns[0]
    first_numeric_col_index = df.columns.get_loc(first_numeric_idx)
    dimension_cols = df.columns[:first_numeric_col_index]

    data_numeric = df.iloc[:, first_numeric_col_index:].apply(pd.to_numeric, errors='coerce')
    results, highlight_flags, explanations = [], [], []

    clf = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        max_samples=min(max_samples, len(data_numeric.columns)),  # auto-adjust
        random_state=random_state
    )

    for i in range(len(data_numeric)):
        row = data_numeric.iloc[i]
        valid = row.dropna()
        non_zero = valid[valid != 0]

        if len(non_zero) < 11:
            results.append("Insufficient Data")
            highlight_flags.append("blue")
            explanations.append("Too few non-zero data points")
        else:
            values = non_zero.values.reshape(-1, 1)
            clf.fit(values)
            prediction = clf.predict(values)
            if prediction[-1] == -1:
                results.append("Anomaly")
                highlight_flags.append("red")
                if values[-1][0] == 0:
                    explanations.append("Missing recent value")
                elif values[-1][0] > values[:-1].mean() * 1.5:
                    explanations.append("Spike in recent period")
                elif values[-1][0] < values[:-1].mean() * 0.5:
                    explanations.append("Consistent drop")
                else:
                    explanations.append("Other")
            else:
                results.append("Normal")
                highlight_flags.append("green")
                explanations.append("")

    df["Anomaly Result"] = results
    df["Anomaly Explanation"] = explanations
    return df, highlight_flags, explanations, list(dimension_cols)
