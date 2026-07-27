import json
import os
import pandas as pd


DEFAULT_RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "lead_time_rules.json")


def load_rules(filepath=None):
    if filepath is None:
        filepath = DEFAULT_RULES_PATH
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as f:
        return json.load(f)


def resolve_lead_time(sap_df, rules):
    sap_df = sap_df.copy()
    if not rules:
        sap_df["lead_time_rule_id"] = None
        sap_df["lead_time_status"] = "No Rules Configured"
        sap_df["lc_due_date"] = pd.NaT
        sap_df["si_due_date"] = pd.NaT
        sap_df["doc_due_date"] = pd.NaT
        return sap_df
    default_rule = None
    for r in rules:
        if r.get("default_rule"):
            default_rule = r
            break
    rule_id_map = {}
    lc_days = []
    si_days = []
    doc_days = []
    rule_ids = []
    statuses = []
    for _, row in sap_df.iterrows():
        material = row.get("material", "")
        source_country = row.get("source_country", "")
        matched = False
        chosen = None
        for r in rules:
            if r.get("material") == material and r.get("source_country") == source_country:
                chosen = r
                matched = True
                break
        if not matched:
            for r in rules:
                if r.get("material") == material:
                    chosen = r
                    matched = True
                    break
        if not matched:
            for r in rules:
                if r.get("source_country") == source_country:
                    chosen = r
                    matched = True
                    break
        if not matched and default_rule is not None:
            chosen = default_rule
            matched = True
        if matched and chosen:
            rule_ids.append(chosen["rule_id"])
            statuses.append("Rule Applied")
            lc_days.append(chosen.get("lc_lead_time_days", 0))
            si_days.append(chosen.get("si_lead_time_days", 0))
            doc_days.append(chosen.get("document_follow_up_days", 0))
            rule_id_map[row.name] = chosen["rule_id"]
        else:
            rule_ids.append(None)
            statuses.append("Data Review Required")
            lc_days.append(0)
            si_days.append(0)
            doc_days.append(0)
    sap_df["lead_time_rule_id"] = rule_ids
    sap_df["lead_time_status"] = statuses
    sap_df["lc_due_date"] = pd.NaT
    sap_df["si_due_date"] = pd.NaT
    sap_df["doc_due_date"] = pd.NaT
    return sap_df
