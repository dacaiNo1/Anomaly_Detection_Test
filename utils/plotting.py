import pandas as pd
import plotly.express as px

def generate_chart(df_results, group_cols, top_n=5, result_filter="All"):
    temp_df = df_results.copy()

    if result_filter != "All":
        temp_df = temp_df[temp_df["Anomaly Result"] == result_filter]

    if not group_cols:
        return None

    # Create composite label
    temp_df["Group_Label"] = temp_df[group_cols].astype(str).agg(" | ".join, axis=1)
    top_labels = temp_df["Group_Label"].value_counts().nlargest(top_n).index.tolist()
    chart_df = temp_df[temp_df["Group_Label"].isin(top_labels)]

    summary = (
        chart_df.groupby(["Group_Label", "Anomaly Result"])
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )

    fig = px.bar(
        summary,
        x="Group_Label",
        y="Count",
        color="Anomaly Result",
        barmode="group",
        color_discrete_map={
            "Anomaly": "red",
            "Normal": "green",
            "Insufficient Data": "blue"
        },
        title="Anomaly Result Count by Group"
    )
    return fig
