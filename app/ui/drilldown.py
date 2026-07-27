import streamlit as st
import pandas as pd


def render(merged_df, eagle_detail_df=None):
    st.header("PO Drill-Down")

    if merged_df is None or merged_df.empty:
        st.info("No data loaded. Upload files on the main page.")
        return

    pos = merged_df["normalized_po"].unique()
    selected_po = st.selectbox("Select a PO to drill into", pos)

    po_data = merged_df[merged_df["normalized_po"] == selected_po]

    if po_data.empty:
        st.warning(f"No data found for PO {selected_po}")
        return

    for _, row in po_data.iterrows():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**SAP Info**")
            st.write(f"**PO:** {row.get('normalized_po', 'N/A')}")
            st.write(f"**Material:** {row.get('material', 'N/A')}")
            st.write(f"**Product:** {row.get('product_description', 'N/A')}")
            st.write(f"**Source Country:** {row.get('source_country', 'N/A')}")
            st.write(f"**Open Qty:** {row.get('open_qty', 'N/A')}")

        with col2:
            st.markdown("**Tracker Timeline**")
            st.write(f"**Overall Status:** {row.get('overall_status', 'N/A')}")
            st.write(f"**LC Date:** {_fmt_date(row.get('lc_date'))}")
            st.write(f"**SI Shared:** {_fmt_date(row.get('si_shared_date'))}")
            st.write(f"**RDD:** {_fmt_date(row.get('tracker_rdd'))}")
            st.write(f"**ETD:** {_fmt_date(row.get('tracker_etd'))}")
            st.write(f"**ETA:** {_fmt_date(row.get('tracker_eta'))}")

        with col3:
            st.markdown("**Eagle Eye**")
            st.write(f"**Status:** {row.get('current_shipment_status', 'N/A')}")
            st.write(f"**ETA:** {_fmt_date(row.get('shipment_eta'))}")
            st.write(f"**Containers:** {row.get('container_count', 'N/A')}")
            st.write(f"**Container(s):** {row.get('container_list', 'N/A')}")
            st.write(f"**ETA Probability:** {row.get('max_eta_probability', 'N/A')}")

    st.markdown("**Exceptions & Actions**")
    st.info(
        f"**Primary Exception:** {po_data.iloc[0].get('primary_exception', 'N/A')}  \n"
        f"**All Exceptions:** {po_data.iloc[0].get('all_exceptions', 'N/A')}  \n"
        f"**Urgency:** {po_data.iloc[0].get('urgency', 'N/A')}  \n"
        f"**Owner:** {po_data.iloc[0].get('recommended_owner', 'N/A')}  \n"
        f"**Action:** {po_data.iloc[0].get('recommended_next_action', 'N/A')}"
    )

    if eagle_detail_df is not None and not eagle_detail_df.empty:
        ee_rows = eagle_detail_df[eagle_detail_df["normalized_po"] == selected_po]
        if not ee_rows.empty:
            st.subheader("Container Details")
            display_ee = ee_rows[[
                "container_no", "tracking", "status", "eta",
                "eta_probability", "eta_confidence", "atd", "ata",
            ]].copy()
            for col in ["eta", "atd", "ata"]:
                if col in display_ee.columns:
                    display_ee[col] = display_ee[col].apply(_fmt_date)
            display_ee["eta_probability"] = display_ee["eta_probability"].apply(
                lambda x: f"{x:.0%}" if pd.notna(x) else ""
            )
            st.dataframe(display_ee, hide_index=True, use_container_width=True)


def _fmt_date(val):
    if pd.isna(val):
        return "N/A"
    if hasattr(val, "strftime"):
        return val.strftime("%d-%b-%Y")
    return str(val)
