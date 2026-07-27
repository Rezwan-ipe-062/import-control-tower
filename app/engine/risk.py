import json
import os
import pandas as pd
import numpy as np

DEFAULT_THRESHOLDS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "config", "urgency_thresholds.json"
)


def load_thresholds(filepath=None):
    if filepath is None:
        filepath = DEFAULT_THRESHOLDS_PATH
    if not os.path.exists(filepath):
        return {"default": {}}
    with open(filepath, "r") as f:
        return json.load(f)


def _get_threshold(source_country, key, thresholds, default_val):
    per_country = thresholds.get("per_country", {})
    defaults = thresholds.get("default", {})
    if source_country in per_country and key in per_country[source_country]:
        return per_country[source_country][key]
    if key in defaults:
        return defaults[key]
    return default_val


def _days_overdue(date_col, merged_df):
    now = pd.Timestamp.now()
    dates = pd.to_datetime(merged_df[date_col], errors="coerce")
    return (now - dates).dt.days


def evaluate_exceptions(merged_df, thresholds=None):
    if thresholds is None:
        thresholds = load_thresholds()
    df = merged_df.copy()
    now = pd.Timestamp.now()
    exceptions = []
    primary_exceptions = []

    for _, row in df.iterrows():
        exc_list = []
        source = row.get("source_country", "")

        if not row.get("tracker_found", False):
            exc_list.append("No Tracker Entry")

        if not row.get("eagle_eye_found", False):
            exc_list.append("No Eagle Eye Entry")

        lc_date = pd.to_datetime(row.get("lc_date"), errors="coerce")
        si_date = pd.to_datetime(row.get("si_shared_date"), errors="coerce")
        eta = pd.to_datetime(row.get("tracker_eta"), errors="coerce")
        status_str = str(row.get("current_shipment_status", ""))
        status_num = 0
        match = pd.Series([status_str]).str.extract(r"(\d+)", expand=False)
        if match.notna().any():
            try:
                status_num = int(match.iloc[0])
            except (ValueError, TypeError):
                status_num = 0

        if pd.notna(lc_date) and pd.isna(si_date):
            lc_overdue = (now - lc_date).days
            if lc_overdue > 0:
                crit = _get_threshold(source, "lc_overdue_critical_days", thresholds, 7)
                urg = _get_threshold(source, "lc_overdue_urgent_days", thresholds, 3)
                if lc_overdue >= crit:
                    exc_list.append(f"LC Overdue ({lc_overdue}d)")
                elif lc_overdue >= urg:
                    exc_list.append(f"LC Overdue ({lc_overdue}d)")

        if pd.notna(si_date) and status_num < 6:
            si_overdue = (now - si_date).days
            if si_overdue > 0:
                crit = _get_threshold(source, "si_overdue_critical_days", thresholds, 7)
                urg = _get_threshold(source, "si_overdue_urgent_days", thresholds, 3)
                if si_overdue >= crit:
                    exc_list.append(f"SI Overdue ({si_overdue}d)")
                elif si_overdue >= urg:
                    exc_list.append(f"SI Overdue ({si_overdue}d)")

        if pd.notna(eta) and status_num < 6:
            eta_overdue = (now - eta).days
            if eta_overdue > 0:
                crit = _get_threshold(source, "eta_overdue_critical_days", thresholds, 14)
                urg = _get_threshold(source, "eta_overdue_urgent_days", thresholds, 7)
                if eta_overdue >= crit:
                    exc_list.append(f"ETA Overdue ({eta_overdue}d)")
                elif eta_overdue >= urg:
                    exc_list.append(f"ETA Overdue ({eta_overdue}d)")

        eta_prob = row.get("max_eta_probability")
        if pd.notna(eta_prob) and status_num < 4:
            crit = _get_threshold(source, "eta_probability_critical", thresholds, 0.3)
            urg = _get_threshold(source, "eta_probability_urgent", thresholds, 0.5)
            imp = _get_threshold(source, "eta_probability_important", thresholds, 0.7)
            if eta_prob <= crit:
                exc_list.append(f"Low ETA Probability ({eta_prob:.0%})")
            elif eta_prob <= urg:
                exc_list.append(f"Low ETA Probability ({eta_prob:.0%})")
            elif eta_prob <= imp:
                exc_list.append(f"Low ETA Probability ({eta_prob:.0%})")

        if not exc_list:
            exc_list.append("On Track")

        exceptions.append("; ".join(exc_list))
        primary_exceptions.append(exc_list[0])

    df["all_exceptions"] = exceptions
    df["primary_exception"] = primary_exceptions

    urgency_map = {
        "No Tracker Entry": "Critical",
        "LC Overdue": "Critical",
        "SI Overdue": "Critical",
        "ETA Overdue": "Critical",
        "No Eagle Eye Entry": "Urgent",
        "Low ETA Probability": "Urgent",
        "On Track": "Normal",
    }
    owner_map = {
        "No Tracker Entry": "Planning Manager",
        "LC Overdue": "Supply Chain",
        "SI Overdue": "Supply Chain",
        "ETA Overdue": "Imports Team",
        "No Eagle Eye Entry": "Planning Manager",
        "Low ETA Probability": "Imports Team",
        "On Track": "Planning Manager",
    }
    action_map = {
        "No Tracker Entry": "Create tracker entry for PO",
        "LC Overdue": "Follow up on LC issuance",
        "SI Overdue": "Follow up on SI submission",
        "ETA Overdue": "Expedite shipment tracking",
        "No Eagle Eye Entry": "Add PO to Eagle Eye monitoring",
        "Low ETA Probability": "Review contingency plan",
        "On Track": "Monitor regularly",
    }

    def resolve(key):
        for exc_type in key.split("; ")[0].split(" (")[0].strip():
            pe = key.split(";")[0].split(" (")[0].strip()
            return pe
        return "On Track"

    df["urgency"] = df["primary_exception"].map(
        lambda x: urgency_map.get(x.split(" (")[0].strip(), "Important")
    )
    df["recommended_owner"] = df["primary_exception"].map(
        lambda x: owner_map.get(x.split(" (")[0].strip(), "Planning Manager")
    )
    df["recommended_next_action"] = df["primary_exception"].map(
        lambda x: action_map.get(x.split(" (")[0].strip(), "Review")
    )
    return df
