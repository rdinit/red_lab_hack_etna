import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from detectors.isolation_forest import isolation_forest

from etna_anomaly_detector.metrics_collection import create_database, select_metric


@st.cache
def create_database_st():
    create_database()


@st.cache_data
def get_data(selected_segment):
    return select_metric(selected_segment)


@st.cache_data
def detect_anomalies(df, start_datetime, end_datetime):
    series = df[start_datetime:end_datetime]
    index = series.index

    mask, _, _ = isolation_forest(
        series=series,
        contamination=0.005,
        n_jobs=-1,
        random_state=1,
        use_time=False,
        use_hw=True,
        # use_stl=True,
        # period=60 * 24,
        period=None,
        trend="add",
        seasonal="add",
    )

    return index[mask]


create_database_st()

st.title("Red Lab Hack Solution")
selected_segment = st.selectbox("Select metric", ("web_response", "throughput", "apdex", "error"))

df = get_data(selected_segment)

start_date = st.date_input("Enter start date", value=df.index.min())
start_time = st.time_input("Enter start time", value=df.index.min())
start_datetime = datetime.datetime.combine(start_date, start_time)

end_date = st.date_input("Enter end date", value=df.index.max())
end_time = st.time_input("Enter end time", value=df.index.max())
end_datetime = datetime.datetime.combine(end_date, end_time)


fig = px.line(x=df.index, y=df.values)
fig.add_vrect(
    x0=start_datetime,
    x1=end_datetime,
    fillcolor="green",
    opacity=0.25,
    line_width=0,
)
fig.update_xaxes(rangeslider_visible=True)
fig.update_yaxes(title=selected_segment)

st.plotly_chart(fig, use_container_width=True)

response = st.button(
    "Search Anomalies",
    type="primary",
)

if response:
    anomalies = detect_anomalies(df=df, start_datetime=start_datetime, end_datetime=end_datetime)
    if len(anomalies) > 0:
        fig = px.line(x=df.index, y=df.values)
        fig.add_scatter(
            x=anomalies, y=df[df.index.isin(anomalies)].values, marker_color="red", mode="markers", showlegend=False
        )
        fig.add_vrect(
            x0=start_datetime,
            x1=end_datetime,
            fillcolor="green",
            opacity=0.25,
            line_width=0,
        )

        fig.update_xaxes(rangeslider_visible=True)
        fig.update_yaxes(title=selected_segment)

        st.plotly_chart(fig, use_container_width=True)
        st.write("Detected anomalies:")
        st.write(pd.Series(anomalies))
    else:
        st.write("Anomalies not detected!")
