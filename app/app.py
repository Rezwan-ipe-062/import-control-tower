import os
import sys
import tempfile
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from engine.loader import load_all
from engine.lead_times import load_rules, resolve_lead_time
from engine.merger import merge_all
from engine.risk import load_thresholds, evaluate_exceptions
from engine.quality import build_quality_log
from ui import dashboard, drilldown, quality_log, config_page

st.set_page_config(
    page_title="Import Control Tower",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Import Control Tower")
st.caption("Unified import tracking for Bangladesh — SAP, BD Tracker & Eagle Eye")


def _resolve_pm_path():
    local_pm = os.path.join(os.path.dirname(__file__), "reference", "product_master.xlsx")
    if os.path.exists(local_pm):
        return local_pm
    return None


def run_pipeline(sap_file, tracker_file, eagle_file, pm_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(sap_file.getbuffer())
        sap_path = tmp.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(tracker_file.getbuffer())
        tracker_path = tmp.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(eagle_file.getbuffer())
        eagle_path = tmp.name

    if pm_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(pm_file.getbuffer())
            pm_path = tmp.name
    else:
        pm_path = _resolve_pm_path()

    if pm_path is None or not os.path.exists(pm_path):
        st.error("Product Master is required. Upload it or ensure reference/product_master.xlsx exists.")
        return None, None, None, None, None, None

    with st.spinner("Loading files..."):
        sap_df, tracker_df, eagle_detail_df, eagle_summary_df, product_master_df = load_all(
            sap_path, tracker_path, eagle_path, pm_path
        )

    with st.spinner("Resolving lead time rules..."):
        rules = load_rules()
        sap_df = resolve_lead_time(sap_df, rules)

    with st.spinner("Merging data sources..."):
        merged_df = merge_all(sap_df, tracker_df, eagle_summary_df)

    with st.spinner("Evaluating exceptions..."):
        thresholds = load_thresholds()
        merged_df = evaluate_exceptions(merged_df, thresholds)

    with st.spinner("Building quality log..."):
        quality_df = build_quality_log(sap_df, tracker_df, eagle_detail_df, product_master_df)

    for p in [sap_path, tracker_path, eagle_path]:
        try:
            os.unlink(p)
        except OSError:
            pass
    if pm_file is not None:
        try:
            os.unlink(pm_path)
        except OSError:
            pass

    return merged_df, eagle_detail_df, quality_df, sap_df, tracker_df, product_master_df


if "pipeline_complete" not in st.session_state:
    st.session_state.pipeline_complete = False
    st.session_state.merged_df = None
    st.session_state.eagle_detail_df = None
    st.session_state.quality_df = None
    st.session_state.sap_df = None
    st.session_state.tracker_df = None
    st.session_state.product_master_df = None

with st.sidebar:
    st.header("Data Upload")
    st.caption("Upload the latest Excel files from each source.")

    sap_file = st.file_uploader("SAP Open PO", type=["xlsx", "xls"], key="sap")
    tracker_file = st.file_uploader("BD Tracker", type=["xlsx", "xls"], key="tracker")
    eagle_file = st.file_uploader("Eagle Eye", type=["xlsx", "xls"], key="eagle")
    pm_override = st.file_uploader(
        "Product Master (optional override)", type=["xlsx", "xls"], key="pm"
    )

    has_pm = pm_override is not None or _resolve_pm_path() is not None
    all_uploaded = all([sap_file, tracker_file, eagle_file])

    if st.button("Run Import Control Tower", type="primary", disabled=not (all_uploaded and has_pm),
                 use_container_width=True):
        result = run_pipeline(sap_file, tracker_file, eagle_file, pm_override)
        merged_df, eagle_detail_df, quality_df, sap_df, tracker_df, pm_df = result
        if merged_df is not None:
            st.session_state.merged_df = merged_df
            st.session_state.eagle_detail_df = eagle_detail_df
            st.session_state.quality_df = quality_df
            st.session_state.sap_df = sap_df
            st.session_state.tracker_df = tracker_df
            st.session_state.product_master_df = pm_df
            st.session_state.pipeline_complete = True
            st.success("Pipeline complete!")
            st.rerun()

    st.divider()
    pm_path_display = _resolve_pm_path()
    if pm_path_display:
        st.caption(f"Product Master: `{os.path.basename(pm_path_display)}`")
    elif pm_override:
        st.caption("Product Master: uploaded (session only)")
    else:
        st.caption("Product Master: Not loaded — upload or place in reference/")

    if not all_uploaded:
        st.caption("Upload SAP, Tracker, and Eagle Eye files to begin.")
    elif not has_pm:
        st.caption("Upload a Product Master file to begin.")

if st.session_state.pipeline_complete and st.session_state.merged_df is not None:
    tab_dash, tab_drill, tab_quality, tab_config = st.tabs([
        "Dashboard", "PO Drill-Down", "Data Quality", "Settings"
    ])

    with tab_dash:
        dashboard.render(st.session_state.merged_df)

    with tab_drill:
        drilldown.render(st.session_state.merged_df, st.session_state.eagle_detail_df)

    with tab_quality:
        quality_log.render(st.session_state.quality_df)

    with tab_config:
        config_page.render(st.session_state.merged_df, st.session_state.product_master_df)
else:
    st.info(
        "Upload your SAP Open PO, BD Tracker, and Eagle Eye Excel files in the sidebar "
        "and click **Run Import Control Tower** to start."
    )
    st.markdown("""
    **How it works:**
    1. Download the latest 4 Excel files from their respective sources
    2. Upload them in the sidebar (Product Master is optional if saved as reference)
    3. Click "Run Import Control Tower" to process and see results
    4. The Dashboard tab shows the prioritised action list
    5. PO Drill-Down lets you inspect individual purchase orders
    6. Settings lets you configure urgency thresholds per source country
    """)
