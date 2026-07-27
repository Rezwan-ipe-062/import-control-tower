# Power Query Guide — Import Control Tower

> Connect and clean all 4 Excel files into one master table using Power Query (Excel Get & Transform or Power BI).

## Setup

1. Open a **blank Excel workbook** → **Data** tab → **Get Data** → **From File** → **From Excel Workbook**
2. Repeat for each source file — or combine into one query later
3. Work from a **copy** of your files (Power Query makes no changes to originals)

---

## Step 1 — SAP Open-PO (master source)

**Goal:** Read only 4 columns, normalize PO, exclude 62-prefix POs, cross-ref to Product Master AGI.

### Load & clean
1. **Get Data** → **From Excel Workbook** → select `SAP Open-PO.xlsx`
2. In Navigator, select the **"Open PO"** sheet → click **Transform Data**
3. Keep only columns A, B, I, N:
   - Home → **Remove Columns** → **Remove Other Columns**
   - Rename: A → `material`, B → `product_description`, I → `purchasing_document`, N → `open_qty`
4. Filter out blanks: Click filter arrow on `purchasing_document` → uncheck null/blank
5. **Normalize PO to 10 digits:**
   - **Add Column** → **Custom Column**
   - New column name: `normalized_po`
   - Formula: `= Text.PadStart(Text.From([purchasing_document]), 10, "0")`
6. **Exclude 62-prefix POs:**
   - **Add Column** → **Custom Column**
   - New column name: `in_scope`
   - Formula: `= not Text.StartsWith([normalized_po], "62")`
   - Click filter arrow on `in_scope` → check only `true`
   - (Optional) Delete the `in_scope` column afterward
7. **Strip leading zeros from Material for AGI cross-ref:**
   - **Add Column** → **Custom Column**
   - New column name: `material_norm`
   - Formula: `= Text.TrimStart([material], "0")`
   - Change data type to **Whole Number** (this makes it match PM's integer AGI)

> **Verify:** `material` = "0093171" → `material_norm` = 93171

---

## Step 2 — BD Tracker

**Goal:** Use only the "Tracker file" sheet, skip 1M blank rows, extract 10-digit PO.

### Load & clean
1. **Get Data** → **From Excel Workbook** → select `BD Tracker.xlsx`
2. In Navigator, select **"Tracker file"** sheet → **Transform Data**
3. **Skip blank rows** (critical — ~94% are empty):
   - Click filter arrow on column A (Overall Status) → uncheck null/blank
4. **Normalize PO (column C):**
   - Column C header has a leading space: rename ` PO` → `original_tracker_po`
   - **Add Column** → **Custom Column**
   - New column name: `normalized_po`
   - Formula: `= Text.Start(Text.Trim([original_tracker_po]), 10)`
   - *(Trims space, takes first 10 digits — handles "6590028515 - 2" → "6590028515")*
5. **Rename key columns** (matching our schema):
   - A → `overall_status`
   - L → `lc_date`, set type to **Date**
   - M → `si_shared_date`, set type to **Date**
   - N → `tracker_rdd`, set type to **Date**
   - O → `tracker_etd`, set type to **Date**
   - P → `tracker_eta`, set type to **Date**
   - S → `obl_ebl_received_date`, set type to **Date**
   - T → `final_docs_received_date`, set type to **Date**
6. Remove all other columns
7. **Change type** for all date columns to **Date** (Home → Data Type)

> **Verify:** Row count drops from 1M+ to ~few hundred (only those matching SAP POs after merge).

---

## Step 3 — Eagle Eye

**Goal:** Handle "-" values, parse status, extract 10-digit PO.

### Load & clean
1. **Get Data** → **From Excel Workbook** → select `Eagle Eye.xlsx`
2. In Navigator, select **"Sheet1"** → **Transform Data**
3. **Normalize PO from column C (DDPO):**
   - **Add Column** → **Custom Column**
   - New column name: `normalized_po`
   - Formula: `= Text.Start(Text.From([Column C]), 10)`
4. **Handle "-" values in dates:**
   - Select date columns (Q, T, W) → **Transform** → **Replace Values**
   - Value to find: `-` → Replace with: (leave blank)
   - Then set type to **Date**
5. **Handle "-" in Probability of Meeting ETA (column U):**
   - Select column U → Replace Values: `-` → (leave blank)
   - Set type to **Decimal** or **Percentage**
6. **Rename key columns:**
   - G → `container_no`
   - H → `tracking_link`
   - I → `status`
   - Q → `atd`
   - T → `eta`
   - U → `eta_probability`
   - V → `eta_confidence`
   - W → `ata`
   - AC → `order_qty`
7. Remove all other columns

> **Note:** This is the detail table (one row per container). We'll aggregate it during merge.

---

## Step 4 — Product Master (reference)

**Goal:** Extract AGI code → Source Country mapping.

### Load & clean
1. **Get Data** → **From Excel Workbook** → select `Product_Master.xlsx`
2. In Navigator, select **"Master"** sheet → **Transform Data**
3. Keep only columns needed for cross-ref:
   - Remove all except C (AGI code), F (Source Country), B (Product Description), E (Brand)
4. **Clean AGI code:**
   - Column C → set type to **Whole Number** (this is the integer AGI)
5. **Rename:**
   - C → `agi_code`
   - F → `source_country`
   - B → `pm_description`
   - E → `brand`
6. Remove duplicates (one AGI per country — safe to keep first):
   - Select `agi_code` column → Home → **Remove Rows** → **Remove Duplicates**

> **Verify:** 68 products should be in the file.

---

## Step 5 — Merge SAP + Product Master (AGI cross-ref)

**Goal:** Assign Source Country to each SAP material.

1. In the SAP query, **Merge Queries**:
   - Home → **Merge Queries** → **Merge Queries as New**
   - Top table: SAP query
   - Bottom table: Product Master query
   - Match: SAP.`material_norm` = PM.`agi_code`
   - Join kind: **Left Outer** (all SAP rows, PM data where matched)
   - Click OK
2. Expand the new column (table icon in header):
   - Check only `source_country` and `pm_description`
   - Uncheck "Use original column name as prefix"
   - Click OK
3. **Flag unmatched:**
   - **Add Column** → **Custom Column**
   - New column name: `agi_status`
   - Formula:
     ```
     = if [source_country] = null then "Unmatched" else "Matched"
     ```

> **Verify:** Source Country fills for ~47 rows, 14 show "Unmatched".

---

## Step 6 — Create Eagle Eye Summary

**Goal:** One row per PO with aggregated container info.

1. Right-click the Eagle Eye query → **Reference**
2. Rename the new query to `Eagle Eye Summary`
3. **Group By:**
   - Home → **Group By**
   - Group by: `normalized_po`
   - New column names:
     - `container_count` → Operation: **Count Rows**
     - `container_list` → Operation: **All Rows** (advanced)
     - `min_eta` → Operation: **Min** → Column: `eta`
     - `min_eta_probability` → Operation: **Min** → Column: `eta_probability`
4. For `container_list`, after grouping:
   - Click **Expand** (table icon) → choose only `container_no` and `tracking_link`
   - Then **Merge Columns** (comma-separated)
5. **Current shipment status:**
   - **Add Column** → **Custom Column**
   - Formula logic (status priority: 6=highest):
     ```
     = try List.Max(Table.Column([container_list], "status")) otherwise null
     ```
   - *(Or skip this and pull the max status value during grouping)*

> **Simpler alternative:** Skip the summary query and just use Eagle Eye detail directly in the final merge — the `risk.py` engine in Python computes summary.

---

## Step 7 — Final Merge (Master Table)

**Goal:** SAP-first LEFT JOIN with Tracker + Eagle Eye.

1. From the SAP+PM merged query: Home → **Merge Queries** → **Merge Queries as New**
2. **First merge — Tracker:**
   - SAP query × Tracker query
   - Match: `normalized_po` on both sides
   - Join kind: **Left Outer**
   - Click OK
   - Expand: select all Tracker columns except `normalized_po`
3. **Second merge — Eagle Eye:**
   - From the result above, Merge again:
   - Current query × Eagle Eye Summary (or Detail)
   - Match: `normalized_po`
   - Join kind: **Left Outer**
   - Expand: select all Eagle Eye columns except `normalized_po`
4. **Rename final columns** for readability:
   - `source_country` → keep
   - `agi_status` → keep
   - All Tracker and Eagle Eye columns as loaded

---

## Step 8 — Load to Excel

1. Home → **Close & Load** → **Close & Load To...**
2. Choose **Table** → **New worksheet**
3. Name the sheet `Active_PO_Control_Table`

You now have a single master table with 4-source cross-reference, ready for:
- PivotTables for executive summary
- Conditional formatting for urgency
- Filters for review by owner/exception
- Export to any format

---

## Quick reference — Applied Steps summary

| Step | SAP | Tracker | Eagle Eye | Product Master |
|------|-----|---------|-----------|----------------|
| Sheet | "Open PO" | "Tracker file" | "Sheet1" | "Master" |
| PO column | I (10 digits) | C (trim + first 10) | C (first 10) | — |
| Keep cols | A, B, I, N | A, L, M, N, O, P, S, T | G, H, I, Q, T, U, V, W, AC | C, F, B, E |
| Key filter | Exclude 62-prefix | Uncheck blank Overall Status | Replace "-" with null | Remove dups on AGI |
| Add derived | material_norm | normalized_po | normalized_po | — |
| Cross-ref | material_norm → PM.agi_code | — | — | agi_code (int) |

## Tips
- Date columns showing as text? Use **Transform** → **Date** → **Parse** for stubborn formats
- To refresh: **Data** → **Refresh All** (or right-click query → Refresh)
- To see M code: **View** → **Advanced Editor** (good for learning the language)
- Always keep a copy of the original files — Power Query reads only, but safer to back up
