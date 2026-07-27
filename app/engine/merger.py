import pandas as pd


SUMMARY_COLS = [
    "normalized_po", "container_count", "container_list", "tracking_link_list",
    "current_shipment_status", "shipment_eta",
]


def merge_sap_tracker(sap_df, tracker_df):
    if tracker_df.empty:
        sap_df["tracker_found"] = False
        sap_df["original_tracker_po"] = None
        sap_df["overall_status"] = None
        sap_df["lc_date"] = pd.NaT
        sap_df["si_shared_date"] = pd.NaT
        sap_df["tracker_rdd"] = pd.NaT
        sap_df["tracker_etd"] = pd.NaT
        sap_df["tracker_eta"] = pd.NaT
        sap_df["obl_ebl_received_date"] = pd.NaT
        sap_df["final_docs_received_date"] = pd.NaT
        return sap_df
    tracker_agg = tracker_df.groupby("normalized_po").agg(
        original_tracker_po=("original_tracker_po", "first"),
        overall_status=("overall_status", "first"),
        lc_date=("lc_date", "first"),
        si_shared_date=("si_shared_date", "first"),
        tracker_rdd=("tracker_rdd", "first"),
        tracker_etd=("tracker_etd", "first"),
        tracker_eta=("tracker_eta", "first"),
        obl_ebl_received_date=("obl_ebl_received_date", "first"),
        final_docs_received_date=("final_docs_received_date", "first"),
    ).reset_index()
    merged = sap_df.merge(tracker_agg, on="normalized_po", how="left")
    merged["tracker_found"] = merged["original_tracker_po"].notna()
    return merged


def merge_eagle(merged_df, eagle_summary_df):
    if eagle_summary_df.empty:
        merged_df["eagle_eye_found"] = False
        for col in SUMMARY_COLS:
            if col != "normalized_po":
                merged_df[col] = None
        return merged_df
    merged = merged_df.merge(eagle_summary_df, on="normalized_po", how="left")
    merged["eagle_eye_found"] = merged["container_count"].notna()
    return merged


def data_visibility_status(merged_df):
    def visibility(row):
        if not row.get("tracker_found", False) and not row.get("eagle_eye_found", False):
            return "SAP Only"
        if row.get("tracker_found", False) and not row.get("eagle_eye_found", False):
            return "SAP + Tracker"
        if not row.get("tracker_found", False) and row.get("eagle_eye_found", False):
            return "SAP + Eagle Eye"
        return "Full Visibility"
    merged_df["data_visibility_status"] = merged_df.apply(visibility, axis=1)
    return merged_df


def merge_all(sap_df, tracker_df, eagle_summary_df, lead_times_df=None):
    merged = merge_sap_tracker(sap_df, tracker_df)
    merged = merge_eagle(merged, eagle_summary_df)
    merged = data_visibility_status(merged)
    return merged
