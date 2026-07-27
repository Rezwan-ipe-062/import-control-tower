import pandas as pd
import numpy as np


def read_sap(filepath):
    xl = pd.ExcelFile(filepath)
    sheet_name = "Open PO" if "Open PO" in xl.sheet_names else xl.sheet_names[0]
    df = pd.read_excel(
        filepath,
        sheet_name=sheet_name,
        usecols="A,B,I,N",
    )
    df.columns = ["material", "product_description", "purchasing_document", "open_qty"]
    df["material"] = df["material"].astype(str).str.strip()
    df["purchasing_document"] = (
        df["purchasing_document"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    )
    df["PO_10digit"] = df["purchasing_document"].str.zfill(10)
    df["normalized_po"] = df["PO_10digit"]
    df["Material_Norm"] = df["material"].str.lstrip("0")
    df["In_Scope"] = ~df["purchasing_document"].str.startswith("62")
    df = df[df["In_Scope"]].copy()
    df["open_qty"] = pd.to_numeric(df["open_qty"], errors="coerce").fillna(0.0)
    return df


def read_tracker(filepath):
    df = pd.read_excel(
        filepath,
        sheet_name="Tracker file",
        usecols="A,C,L,M,N,O,P,S,T",
        dtype=str,
    )
    df.columns = [
        "overall_status", "original_tracker_po", "lc_date", "si_shared_date",
        "tracker_rdd", "tracker_etd", "tracker_eta",
        "obl_ebl_received_date", "final_docs_received_date",
    ]
    df = df[df["overall_status"].notna() & (df["overall_status"].str.strip() != "")].copy()
    date_cols = ["lc_date", "si_shared_date", "tracker_rdd", "tracker_etd", "tracker_eta",
                 "obl_ebl_received_date", "final_docs_received_date"]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["original_tracker_po"] = df["original_tracker_po"].astype(str).str.strip()
    normalized = df["original_tracker_po"].str.extract(r"(\d{10})", expand=False)
    df["normalized_po"] = normalized
    shipment = df["original_tracker_po"].str.extract(r"-\s*(\d+)$", expand=False)
    df["partial_shipment_no"] = pd.to_numeric(shipment, errors="coerce").fillna(0).astype(int)
    df = df[df["normalized_po"].notna()].copy()
    return df


def read_eagle_eye(filepath):
    df = pd.read_excel(
        filepath,
        sheet_name="Sheet1",
        usecols="C,G,H,I,Q,T,U,V,W,AC",
        dtype=str,
    )
    df.columns = [
        "ddpo", "container_no", "tracking", "status",
        "atd", "eta", "eta_probability", "eta_confidence",
        "ata", "order_qty",
    ]
    df["_po_raw"] = df["ddpo"].astype(str).str.strip()
    df["normalized_po"] = df["_po_raw"].str.replace(r"\D", "", regex=True)
    df["normalized_po"] = df["normalized_po"].str.zfill(10).str[:10]
    df = df[df["normalized_po"].notna() & (df["normalized_po"].str.len() == 10)].copy()
    df["ddpo"] = df["ddpo"].astype(str).str.strip()
    df["status"] = df["status"].astype(str).str.strip()
    df["container_no"] = df["container_no"].astype(str).str.strip()
    df["tracking"] = df["tracking"].astype(str).str.strip()
    df["eta_confidence"] = df["eta_confidence"].astype(str).str.strip()
    for col in ["eta", "atd", "ata"]:
        df[col] = df[col].replace("-", np.nan)
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["eta_probability"] = (
        df["eta_probability"]
        .replace("-", np.nan)
        .astype(float)
    )
    df["order_qty"] = pd.to_numeric(df["order_qty"], errors="coerce").fillna(0.0)
    return df


def read_product_master(filepath):
    df = pd.read_excel(
        filepath,
        sheet_name="Master",
        usecols="C,F",
        dtype={0: str, 1: str},
    )
    df.columns = ["agi_code_str", "source_country"]
    df = df.dropna(subset=["agi_code_str"])
    df["agi_code_str"] = df["agi_code_str"].astype(str).str.strip()
    df["AGI_Code"] = pd.to_numeric(df["agi_code_str"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["AGI_Code"]).drop_duplicates(subset="AGI_Code").copy()
    return df[["AGI_Code", "source_country"]]


def cross_reference_agi(sap_df, product_master_df):
    sap_df = sap_df.copy()
    sap_df["AGI_Code"] = pd.to_numeric(sap_df["Material_Norm"], errors="coerce").astype("Int64")
    agi_map = product_master_df.set_index("AGI_Code")["source_country"].to_dict()
    sap_df["source_country"] = sap_df["AGI_Code"].map(agi_map)
    sap_df["AGI_Matched"] = sap_df["source_country"].notna()
    return sap_df


def summarize_eagle(eagle_detail_df):
    if eagle_detail_df.empty:
        return pd.DataFrame(columns=[
            "normalized_po", "container_count", "container_list", "tracking_link_list",
            "current_shipment_status", "shipment_eta",
            "min_eta_probability", "max_eta_probability",
        ])
    def max_status(s):
        nums = pd.to_numeric(s.str.extract(r"(\d+)", expand=False), errors="coerce")
        return int(nums.max()) if nums.notna().any() else 0
    summary = eagle_detail_df.groupby("normalized_po").agg(
        container_count=("container_no", "count"),
        container_list=("container_no", lambda x: ", ".join(x.dropna().unique())),
        tracking_link_list=("tracking", lambda x: ", ".join(x.dropna().unique())),
        current_shipment_status=("status", max_status),
        shipment_eta=("eta", "min"),
        min_eta_probability=("eta_probability", "min"),
        max_eta_probability=("eta_probability", "max"),
    ).reset_index()
    return summary


def load_all(sap_path, tracker_path, eagle_path, pm_path):
    sap_df = read_sap(sap_path)
    tracker_df = read_tracker(tracker_path)
    eagle_detail_df = read_eagle_eye(eagle_path)
    product_master_df = read_product_master(pm_path)
    sap_df = cross_reference_agi(sap_df, product_master_df)
    eagle_summary_df = summarize_eagle(eagle_detail_df)
    return sap_df, tracker_df, eagle_detail_df, eagle_summary_df, product_master_df
