# Database

> Data model for the Import Control Tower. No traditional SQL database — data lives in pandas DataFrames (in-memory during session) and JSON config files (persistent). This file documents the schema contracts.

## Conventions
- **Primary key concept:** Normalized_PO + Material (SAP grain) for Active_PO_Control_Table
- **No database:** All data loaded from uploaded Excel files, processed in pandas, and stored in-memory during the Streamlit session
- **Persistence:** One JSON config file (lead_time_rules.json) and the Product Master Excel file are persisted to disk. scope_mapping.json removed — 62-prefix exclusion is now a hard rule.
- **Naming:** Snake_case for DataFrame columns, PascalCase for JSON keys

## JSON Config Files (persisted to `config/`)

### lead_time_rules.json
Stored as an array of rule objects:

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| rule_id | int | yes | Auto-increment |
| material | str | no | SKU-specific rule |
| product_family | str | no | Product group |
| source_country | str | no | e.g. "Syngenta, India", "Syngenta, China" |
| supply_scenario | str | no | e.g. "Normal", "Express" |
| lc_lead_time_days | int | yes | Days from PO date to LC deadline |
| si_lead_time_days | int | yes | Days from LC to SI deadline |
| document_follow_up_days | int | yes | Days after ETD before docs must be received |
| default_rule | bool | no | Only one rule should be marked as default |

Rule precedence (applied in order):
1. Material + Source Country match
2. Material only match
3. Source Country only match
4. Default rule
5. No match → "Data Review Required"

## In-Memory DataFrames (session-only, not persisted)

### Source A: sap_df
One row per SAP PO + Material. Read from SAP Open-PO.xlsx, sheet "Open PO".

| Column | SAP Name | Excel Col | Type | Notes |
|--------|----------|-----------|------|-------|
| material | Material | A | str(7) | 7-digit material code, often with leading zeros |
| product_description | Short Text | B | str | Material description |
| purchasing_document | Purchasing Document | I | str(10) | Raw PO number |
| open_qty | Still to be delivered (qty) | N | float | Open qty in base UoM |

**Derived columns added during loading:**
- `PO_10digit` — purchasing_document zero-padded to 10 digits
- `Normalized_PO` — PO_10digit (merge key)
- `In_Scope` — True if PO does NOT start with "62" (hard-excluded)
- `Material_Norm` — Material stripped of leading zeros (used for AGI cross-ref)
- `AGI_Code` — integer version of Material_Norm
- `source_country` — resolved from Product Master via AGI lookup

### Source B: tracker_df
One row per Tracker line (can have multiple partial shipments per PO). Read from BD Tracker.xlsx, sheet "Tracker file".

| Column | Excel Col | Type | Notes |
|--------|-----------|------|-------|
| overall_status | A | str | |
| original_tracker_po | C | str | e.g. "6590028515 - 2" |
| normalized_po | derived | str | First 10 digits |
| partial_shipment_no | derived | int | Suffix after " - " |
| lc_date | L | datetime | |
| si_shared_date | M | datetime | |
| tracker_rdd | N | datetime | |
| tracker_etd | O | datetime | |
| tracker_eta | P | datetime | |
| obl_ebl_received_date | S | datetime | |
| final_docs_received_date | T | datetime | |

### Source C: eagle_detail_df
One row per container per PO. Read from Eagle Eye.xlsx, sheet "Sheet1".

| Column | Excel Col | Type | Notes |
|--------|-----------|------|-------|
| normalized_po | derived from C | str | First 10 digits of DDPO |
| container_no | G | str | |
| tracking | H | str | |
| status | I | str | "1 Pending TP Flag / CCR" through "6 Arrived at Door" |
| eta | T | datetime | |
| eta_probability | U | float | 0.0-1.0. Only for status 1-3. |
| eta_confidence | V | str | High/Medium/Low |
| atd | Q | datetime | Actual departure (status 4+) |
| ata | W | datetime | Actual arrival (status 5-6) |
| order_qty | AC | float | |

### Source D: eagle_summary_df
One row per normalized_po. Aggregated from eagle_detail_df.

| Column | Derivation |
|--------|-----------|
| normalized_po | |
| container_count | Count of rows |
| container_list | Comma-separated |
| tracking_link_list | Comma-separated |
| current_shipment_status | Highest-priority status (6=highest, 1=lowest) |
| shipment_eta | Earliest ETA |
| min_eta_probability | Lowest probability of meeting ETA |
| max_eta_probability | Highest probability |

### Active_PO_Control_Table (final merged output)
One row per SAP PO + Material. Grain = sap_df rows.

| Field Category | Fields |
|---|---|
| SAP data | normalized_po, material, product_description, supplier, open_qty, order_unit, sap_delivery_date |
| Tracker data | original_tracker_po, partial_shipment_no, overall_status, lc_date, si_shared_date, tracker_rdd, tracker_etd, tracker_eta, obl_ebl_received_date, final_docs_received_date |
| Eagle Eye summary | container_count, container_list, tracking_link_list, current_shipment_status, shipment_eta |
| Derived | tracker_found, eagle_eye_found, data_visibility_status, days_to_rtd |
| Risk | primary_exception, all_exceptions, urgency, recommended_owner, recommended_next_action |
| Meta | refresh_as_of_date |

## Relationships (join keys)
- `sap_df.normalized_po` → `tracker_df.normalized_po` (1-to-many — one SAP PO can have multiple partial shipments)
- `sap_df.normalized_po` → `eagle_summary_df.normalized_po` (1-to-1)
- `eagle_summary_df.normalized_po` → `eagle_detail_df.normalized_po` (1-to-many)

## Indexes (for performance)
Not applicable — DataFrames are small (~150 rows for SAP, ~165 for Eagle Eye). Tracker file is large (1M+ rows) but filtered early by matching against SAP normalized POs.

## Data quality checks (applied during load)
- Tracker file: skip rows with blank Overall Status to avoid 1M+ empty rows
- Eagle Eye: gracefully handle "-" values for dates and probabilities
- SAP: POs with 62 prefix (tolling/manufacturing) hard-excluded
