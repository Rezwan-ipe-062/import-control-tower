import json
import os
import streamlit as st
import pandas as pd

THRESHOLDS_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "urgency_thresholds.json")
RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "lead_time_rules.json")


def _load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def render(merged_df=None, product_master_df=None):
    st.header("Settings")

    tab1, tab2, tab3 = st.tabs(["Urgency Thresholds", "Lead Time Rules", "Product Master"])

    with tab1:
        _render_urgency_thresholds()

    with tab2:
        _render_lead_time_rules()

    with tab3:
        _render_product_master(product_master_df)


def _render_urgency_thresholds():
    thresholds = _load_json(THRESHOLDS_PATH)
    defaults = thresholds.get("default", {})
    per_country = thresholds.get("per_country", {})

    st.subheader("Urgency Thresholds")
    st.caption("Set the day thresholds for each urgency level per source country. "
               "Changes are saved to a local JSON file and persist between sessions.")

    countries = list(per_country.keys())
    selected = st.selectbox(
        "Source Country",
        ["Default"] + countries + ["Add new country..."],
        key="urgency_country_select"
    )

    if selected == "Add new country...":
        new = st.text_input("Enter new source country name", key="new_country_input")
        if new and st.button("Add Country", key="add_country_btn"):
            if new not in per_country:
                per_country[new] = {}
                thresholds["per_country"] = per_country
                _save_json(THRESHOLDS_PATH, thresholds)
                st.success(f"Added {new}")
                st.rerun()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**LC Overdue Thresholds**")
        lc_crit_key = "lc_overdue_critical_days"
        lc_urg_key = "lc_overdue_urgent_days"
        if selected == "Default":
            lc_crit_val = defaults.get(lc_crit_key, 7)
            lc_urg_val = defaults.get(lc_urg_key, 3)
        else:
            lc_crit_val = per_country.get(selected, {}).get(lc_crit_key, defaults.get(lc_crit_key, 7))
            lc_urg_val = per_country.get(selected, {}).get(lc_urg_key, defaults.get(lc_urg_key, 3))

        lc_crit = st.number_input("Critical (days)", min_value=1, value=int(lc_crit_val), key="lc_crit")
        lc_urg = st.number_input("Urgent (days)", min_value=1, value=int(lc_urg_val), key="lc_urg")
        st.caption("LC overdue for >= Critical days or >= Urgent days")

        st.markdown("**SI Overdue Thresholds**")
        si_crit_key = "si_overdue_critical_days"
        si_urg_key = "si_overdue_urgent_days"
        if selected == "Default":
            si_crit_val = defaults.get(si_crit_key, 7)
            si_urg_val = defaults.get(si_urg_key, 3)
        else:
            si_crit_val = per_country.get(selected, {}).get(si_crit_key, defaults.get(si_crit_key, 7))
            si_urg_val = per_country.get(selected, {}).get(si_urg_key, defaults.get(si_urg_key, 3))

        si_crit = st.number_input("Critical (days)", min_value=1, value=int(si_crit_val), key="si_crit")
        si_urg = st.number_input("Urgent (days)", min_value=1, value=int(si_urg_val), key="si_urg")
        st.caption("SI overdue for >= Critical days or >= Urgent days")

    with col2:
        st.markdown("**ETA Overdue Thresholds**")
        eta_crit_key = "eta_overdue_critical_days"
        eta_urg_key = "eta_overdue_urgent_days"
        if selected == "Default":
            eta_crit_val = defaults.get(eta_crit_key, 14)
            eta_urg_val = defaults.get(eta_urg_key, 7)
        else:
            eta_crit_val = per_country.get(selected, {}).get(eta_crit_key, defaults.get(eta_crit_key, 14))
            eta_urg_val = per_country.get(selected, {}).get(eta_urg_key, defaults.get(eta_urg_key, 7))

        eta_crit = st.number_input("Critical (days)", min_value=1, value=int(eta_crit_val), key="eta_crit")
        eta_urg = st.number_input("Urgent (days)", min_value=1, value=int(eta_urg_val), key="eta_urg")
        st.caption("ETA overdue for >= Critical days or >= Urgent days")

        st.markdown("**ETA Probability Thresholds**")
        prob_crit_key = "eta_probability_critical"
        prob_urg_key = "eta_probability_urgent"
        prob_imp_key = "eta_probability_important"
        if selected == "Default":
            prob_crit_val = defaults.get(prob_crit_key, 0.3)
            prob_urg_val = defaults.get(prob_urg_key, 0.5)
            prob_imp_val = defaults.get(prob_imp_key, 0.7)
        else:
            prob_crit_val = per_country.get(selected, {}).get(prob_crit_key, defaults.get(prob_crit_key, 0.3))
            prob_urg_val = per_country.get(selected, {}).get(prob_urg_key, defaults.get(prob_urg_key, 0.5))
            prob_imp_val = per_country.get(selected, {}).get(prob_imp_key, defaults.get(prob_imp_key, 0.7))

        prob_crit = st.slider("Critical (≤)", 0.0, 1.0, float(prob_crit_val), 0.05, key="prob_crit")
        prob_urg = st.slider("Urgent (≤)", 0.0, 1.0, float(prob_urg_val), 0.05, key="prob_urg")
        prob_imp = st.slider("Important (≤)", 0.0, 1.0, float(prob_imp_val), 0.05, key="prob_imp")

    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        if st.button("Save Thresholds", type="primary", use_container_width=True):
            if selected == "Default":
                defaults["lc_overdue_critical_days"] = lc_crit
                defaults["lc_overdue_urgent_days"] = lc_urg
                defaults["si_overdue_critical_days"] = si_crit
                defaults["si_overdue_urgent_days"] = si_urg
                defaults["eta_overdue_critical_days"] = eta_crit
                defaults["eta_overdue_urgent_days"] = eta_urg
                defaults["eta_probability_critical"] = prob_crit
                defaults["eta_probability_urgent"] = prob_urg
                defaults["eta_probability_important"] = prob_imp
            else:
                per_country[selected] = {
                    "lc_overdue_critical_days": lc_crit,
                    "lc_overdue_urgent_days": lc_urg,
                    "si_overdue_critical_days": si_crit,
                    "si_overdue_urgent_days": si_urg,
                    "eta_overdue_critical_days": eta_crit,
                    "eta_overdue_urgent_days": eta_urg,
                    "eta_probability_critical": prob_crit,
                    "eta_probability_urgent": prob_urg,
                    "eta_probability_important": prob_imp,
                }
            thresholds["default"] = defaults
            thresholds["per_country"] = per_country
            _save_json(THRESHOLDS_PATH, thresholds)
            st.success("Thresholds saved successfully!")

    with btn_col2:
        if st.button("Reset to Defaults", use_container_width=True):
            _save_json(THRESHOLDS_PATH, {
                "default": {
                    "lc_overdue_critical_days": 7, "lc_overdue_urgent_days": 3,
                    "si_overdue_critical_days": 7, "si_overdue_urgent_days": 3,
                    "eta_overdue_critical_days": 14, "eta_overdue_urgent_days": 7,
                    "eta_probability_critical": 0.3, "eta_probability_urgent": 0.5,
                    "eta_probability_important": 0.7,
                }, "per_country": {}
            })
            st.success("Reset to defaults!")
            st.rerun()

    if selected != "Default" and selected in per_country:
        if st.button(f"Remove '{selected}'", type="secondary", use_container_width=True):
            del per_country[selected]
            thresholds["per_country"] = per_country
            _save_json(THRESHOLDS_PATH, thresholds)
            st.success(f"Removed {selected}")
            st.rerun()


def _render_lead_time_rules():
    rules = _load_json(RULES_PATH)
    st.subheader("Lead Time Rules")
    st.caption("Configure expected lead times by source country. Rules define "
               "how many days are allocated for LC issuance, SI submission, and document follow-up.")

    if not rules:
        st.info("No lead time rules configured yet.")
        return

    df_rules = pd.DataFrame(rules)
    display_cols = ["rule_id", "source_country", "lc_lead_time_days", "si_lead_time_days",
                    "document_follow_up_days", "default_rule"]
    existing = [c for c in display_cols if c in df_rules.columns]
    st.dataframe(df_rules[existing], hide_index=True, use_container_width=True)

    with st.expander("Add / Edit Lead Time Rule"):
        rule_id = st.number_input("Rule ID", min_value=1, value=len(rules) + 1, step=1)
        source = st.text_input("Source Country")
        lc = st.number_input("LC Lead Time (days)", min_value=1, value=30)
        si = st.number_input("SI Lead Time (days)", min_value=1, value=15)
        doc = st.number_input("Document Follow-up (days)", min_value=1, value=10)
        is_default = st.checkbox("Default Rule")

        if st.button("Save Rule", type="primary"):
            existing_ids = [r["rule_id"] for r in rules]
            existing_source = [r.get("source_country") for r in rules]
            if rule_id in existing_ids:
                for r in rules:
                    if r["rule_id"] == rule_id:
                        r.update({"source_country": source, "lc_lead_time_days": lc,
                                  "si_lead_time_days": si, "document_follow_up_days": doc,
                                  "default_rule": is_default})
                        break
            else:
                if is_default:
                    for r in rules:
                        r["default_rule"] = False
                rules.append({"rule_id": rule_id, "source_country": source,
                              "lc_lead_time_days": lc, "si_lead_time_days": si,
                              "document_follow_up_days": doc, "default_rule": is_default})
            _save_json(RULES_PATH, rules)
            st.success("Rule saved!")
            st.rerun()


def _render_product_master(product_master_df=None):
    st.subheader("Product Master")
    st.caption("The Product Master maps AGI codes to Source Countries. "
               "Upload a new version if the reference file changes.")

    if product_master_df is not None and not product_master_df.empty:
        st.dataframe(product_master_df, hide_index=True, use_container_width=True)
        st.download_button(
            "Download Product Master as CSV",
            data=product_master_df.to_csv(index=False),
            file_name="product_master.csv",
            mime="text/csv",
        )
    else:
        st.info("No Product Master data loaded. Upload files on the main page first.")

    uploaded_pm = st.file_uploader(
        "Upload new Product Master (optional, persistent reference)",
        type=["xlsx"], key="pm_upload_settings"
    )
    if uploaded_pm:
        save_path = os.path.join(os.path.dirname(__file__), "..", "reference", "product_master.xlsx")
        with open(save_path, "wb") as f:
            f.write(uploaded_pm.getbuffer())
        st.success(f"Saved as {save_path}. Reload the app to use the new reference file.")
