import streamlit as st
import pandas as pd


def render(quality_df):
    st.header("Data Quality Log")

    if quality_df is None or quality_df.empty:
        st.success("No data quality issues detected.")
        return

    severity_order = {"Error": 0, "Warning": 1, "Info": 2}
    quality_df["_sort"] = quality_df["severity"].map(severity_order).fillna(99)
    sorted_df = quality_df.sort_values("_sort")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Errors", (quality_df["severity"] == "Error").sum())
    with col2:
        st.metric("Warnings", (quality_df["severity"] == "Warning").sum())
    with col3:
        st.metric("Info Items", (quality_df["severity"] == "Info").sum())

    severity_colors = {"Error": "#f8d7da", "Warning": "#fff3cd", "Info": "#d1ecf1"}

    def color_sev(val):
        bg = severity_colors.get(val, "")
        if bg:
            return f"background-color: {bg}"
        return ""

    styled = sorted_df[["severity", "source", "issue", "detail"]].style.applymap(
        color_sev, subset=["severity"]
    )
    st.dataframe(styled, hide_index=True, use_container_width=True)

    csv = sorted_df[["severity", "source", "issue", "detail"]].to_csv(index=False)
    st.download_button(
        "Download Quality Log as CSV", data=csv,
        file_name="data_quality_log.csv", mime="text/csv",
    )
