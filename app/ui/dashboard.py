import streamlit as st
import pandas as pd
import plotly.express as px


def render(merged_df):
    st.header("Executive Dashboard")

    if merged_df is None or merged_df.empty:
        st.info("No data loaded. Upload files on the main page.")
        return

    urgency_counts = merged_df["urgency"].value_counts()
    total_pos = len(merged_df)
    total_open_qty = merged_df["open_qty"].sum()
    critical_count = urgency_counts.get("Critical", 0)
    urgent_count = urgency_counts.get("Urgent", 0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total POs", total_pos)
    with col2:
        st.metric("Open Qty", f"{total_open_qty:,.0f}")
    with col3:
        st.metric("Critical", critical_count, delta_color="inverse")
    with col4:
        st.metric("Urgent", urgent_count, delta_color="inverse")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Exception Breakdown")
        exc_counts = merged_df["primary_exception"].value_counts().reset_index()
        exc_counts.columns = ["Exception", "Count"]
        fig = px.bar(
            exc_counts, x="Exception", y="Count",
            color="Exception", text="Count",
            color_discrete_sequence=px.colors.qualifier.Set2,
        )
        fig.update_layout(showlegend=False, height=350, margin=dict(l=10, r=10, t=10, b=30))
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Data Visibility")
        vis_counts = merged_df["data_visibility_status"].value_counts().reset_index()
        vis_counts.columns = ["Status", "Count"]
        fig2 = px.pie(
            vis_counts, names="Status", values="Count",
            color_discrete_sequence=px.colors.qualifier.Set3,
        )
        fig2.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=30))
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Prioritised Action List")
    urgency_order = {"Critical": 0, "Urgent": 1, "Important": 2, "Normal": 3}
    merged_df["_sort_key"] = merged_df["urgency"].map(urgency_order).fillna(99)
    sorted_df = merged_df.sort_values(["_sort_key", "primary_exception"])

    display_cols = [
        "normalized_po", "material", "product_description", "source_country",
        "open_qty", "primary_exception", "urgency", "recommended_owner",
        "recommended_next_action", "data_visibility_status",
    ]
    existing_cols = [c for c in display_cols if c in sorted_df.columns]
    table_df = sorted_df[existing_cols].copy()

    def color_row(row):
        urgency_val = row.get("urgency", "")
        if urgency_val == "Critical":
            return ["background-color: #f8d7da"] * len(row)
        elif urgency_val == "Urgent":
            return ["background-color: #fff3cd"] * len(row)
        elif urgency_val == "Important":
            return ["background-color: #e8f4f8"] * len(row)
        return [""] * len(row)

    styled = table_df.style.apply(color_row, axis=1)
    st.dataframe(styled, hide_index=True, use_container_width=True, height=500)

    csv = table_df.to_csv(index=False)
    st.download_button(
        "Download as CSV", data=csv,
        file_name="import_control_tower_export.csv", mime="text/csv",
    )

    return sorted_df
