import pandas as pd
import numpy as np


def build_quality_log(sap_df, tracker_df, eagle_detail_df, product_master_df):
    issues = []

    if sap_df.empty:
        issues.append({
            "source": "SAP", "severity": "Error",
            "issue": "SAP file is empty or could not be read",
            "detail": "No purchase order data available for processing",
        })
    else:
        agi_matched = sap_df["AGI_Matched"].sum() if "AGI_Matched" in sap_df.columns else 0
        total = len(sap_df)
        unmatched = total - agi_matched
        if unmatched > 0:
            unmatched_materials = sap_df.loc[
                ~sap_df["AGI_Matched"], "material"
            ].unique().tolist() if "AGI_Matched" in sap_df.columns else []
            issues.append({
                "source": "SAP -> Product Master",
                "severity": "Warning",
                "issue": f"{unmatched} of {total} materials not matched to AGI codes",
                "detail": f"Unmatched materials: {', '.join(str(m) for m in unmatched_materials[:20])}{'...' if len(unmatched_materials) > 20 else ''}",
            })
        no_source = sap_df["source_country"].isna().sum() if "source_country" in sap_df.columns else 0
        if no_source > 0:
            issues.append({
                "source": "SAP", "severity": "Warning",
                "issue": f"{no_source} PO rows have no Source Country assigned",
                "detail": "Lead time rules cannot be resolved for these items",
            })
        zero_qty = (sap_df["open_qty"] == 0).sum() if "open_qty" in sap_df.columns else 0
        if zero_qty > 0:
            issues.append({
                "source": "SAP", "severity": "Info",
                "issue": f"{zero_qty} PO rows have zero open quantity",
                "detail": "These POs may be fully delivered but still open in SAP",
            })

    if tracker_df.empty:
        issues.append({
            "source": "Tracker", "severity": "Warning",
            "issue": "BD Tracker file is empty or could not be read",
            "detail": "No milestone tracking data available",
        })
    else:
        if sap_df is not None and not sap_df.empty:
            sap_pos = set(sap_df["normalized_po"].unique())
            tracker_pos = set(tracker_df["normalized_po"].unique())
            orphan_tracker = tracker_pos - sap_pos
            if orphan_tracker:
                issues.append({
                    "source": "Tracker", "severity": "Info",
                    "issue": f"{len(orphan_tracker)} POs in Tracker not found in SAP",
                    "detail": "These may be historical or non-import POs",
                })
        blank_dates = tracker_df[["lc_date", "si_shared_date"]].isna().all(axis=1).sum()
        if blank_dates > 0:
            issues.append({
                "source": "Tracker", "severity": "Info",
                "issue": f"{blank_dates} tracker entries have no LC or SI dates",
                "detail": "Milestone tracking may be incomplete for these shipments",
            })

    if eagle_detail_df.empty:
        issues.append({
            "source": "Eagle Eye", "severity": "Warning",
            "issue": "Eagle Eye file is empty or could not be read",
            "detail": "No shipment tracking data available",
        })
    else:
        if sap_df is not None and not sap_df.empty:
            sap_pos = set(sap_df["normalized_po"].unique())
            eagle_pos = set(eagle_detail_df["normalized_po"].unique())
            orphan_eagle = eagle_pos - sap_pos
            if orphan_eagle:
                issues.append({
                    "source": "Eagle Eye", "severity": "Info",
                    "issue": f"{len(orphan_eagle)} POs in Eagle Eye not found in SAP",
                    "detail": "These may be completed or non-import shipments",
                })
        invalid_probs = eagle_detail_df["eta_probability"].isna().sum()
        total_ee = len(eagle_detail_df)
        if invalid_probs > 0 and invalid_probs < total_ee:
            issues.append({
                "source": "Eagle Eye", "severity": "Info",
                "issue": f"{invalid_probs} of {total_ee} rows missing ETA probability",
                "detail": "Probability-based risk assessment limited for these shipments",
            })

    if product_master_df.empty:
        issues.append({
            "source": "Product Master", "severity": "Error",
            "issue": "Product Master file is empty or could not be read",
            "detail": "AGI to Source Country mapping unavailable. All POs will have no Source Country.",
        })
    else:
        issues.append({
            "source": "Product Master", "severity": "Info",
            "issue": f"{len(product_master_df)} products loaded with Source Country mapping",
            "detail": f"Countries: {', '.join(product_master_df['source_country'].dropna().unique())}",
        })

    return pd.DataFrame(issues)
