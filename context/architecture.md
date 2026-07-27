# Architecture

> Solution-level design. The map the AI reads before writing any code.

## 1. Overview
- **Product:** Bangladesh Import Control Tower — unifies SAP Open POs, BD Tracker, Eagle Eye, and Product Master into one actionable dashboard for the Planning Manager
- **Core value:** Cross-references 4 disconnected data sources and automatically prioritizes at-risk import POs with root cause, urgency, and recommended owner
- **Scale target (v1):** 4 users, each on their own laptop. ~150 open PO lines per refresh. Weekly file uploads.

## 2. Tech stack
| Layer | Choice | Why |
|-------|--------|-----|
| Front-end + Back-end | Streamlit (Python) | Single language for UI + processing. Runs entirely on localhost. Built-in file uploader. |
| Data processing | pandas, openpyxl | Read/write Excel files, merge data sources, date handling |
| Visualization | Streamlit native + Plotly | Tables, metric cards, bar charts for exception breakdown |
| Packaging | PyInstaller | Wraps Python app into standalone .exe. No Python install on user's PC. |
| Persistence | JSON config files + Product Master Excel | Lead time rules stored as editable JSON. Product Master stored as reference file (re-uploadable via admin). |

## 3. System diagram (data flow)
```
User downloads 4 files from SAP / Tracker / Eagle Eye / Product Master
         |
         v
[ User's Laptop ]
  User double-clicks ImportControlTower.exe
         |
         v
[ Browser opens at localhost:8501 ]

            Upload Page
         User uploads SAP, Tracker, Eagle Eye files
         (Product Master is a one-time reference, re-uploadable via admin)
                 |
                 v
    ┌─────────────────────────────────────┐
    │  Python Processing Engine           │
    │                                     │
    │  Step 1: loader.py                  │
    │   - Read SAP Open-PO (4 columns:    │
    │     Material, Short Text,           │
    │     Purchasing Document, Still to   │
    │     be delivered)                   │
    │   - Read BD Tracker.xlsx            │
    │   - Read Eagle Eye.xlsx             │
    │   - Read Product Master (AGI →      │
    │     Source Country lookup)           │
    │   - Cross-ref SAP Material → PM     │
    │     AGI → Source Country             │
    │   - Normalize PO keys (10 digits)   │
    │   - Parse dates, handle blanks      │
    │   - Exclude 62-prefix POs (tolling) │
    │                                     │
    │  Step 2: lead_times.py              │
    │   - Load Lead_Time_Rules from JSON  │
    │   - Rules keyed on Source Country   │
    │   - Calculate LC/SI/doc deadlines   │
    │                                     │
    │  Step 3: merger.py                  │
    │   - SAP-first LEFT JOIN             │
    │   - Merge Tracker + Eagle Eye       │
    │                                     │
    │  Step 4: risk.py                    │
    │   - Evaluate 6 exception types      │
    │   - Assign urgency + owner + action │
    │                                     │
    │  Step 5: quality.py                 │
    │   - Build data quality log          │
    │   - Track AGI code mismatches       │
    └─────────────────────────────────────┘
                |
                v
    ┌─────────────────────────────────────┐
    │  Dashboard Views                    │
    │                                     │
    │  - Executive Summary (cards+chart)  │
    │  - Prioritised Action List (table)  │
    │  - PO Drill-Down (timeline+detail)  │
    │  - Data Quality Log                 │
    │  - Configuration (edit rules)       │
    └─────────────────────────────────────┘
```

- **Processing Engine responsibilities:** Read/clean/normalize 4 Excel files, cross-reference SAP Material with Product Master AGI codes to determine Source Country, merge on Normalized_PO, resolve lead-time rules, assess risk, assign urgency/owner/action, build data quality log.
- **UI responsibilities:** File upload, display dashboard views, filtering/sorting, drill-down, config editor, Excel export.
- **What NEVER happens on the client:** No cloud calls, no data upload, no secrets, no database writes.

## 4. APIs (contract)
Not applicable — this is a local desktop app with no external API. Streamlit renders server-side and communicates with the browser over localhost WebSocket.

### Internal engine interfaces (between modules):

| Caller → Callee | Input | Output |
|---|---|---|
| app.py → loader | 4 file paths (SAP, Tracker, Eagle Eye, Product Master) | 5 DataFrames (sap, tracker, eagle_detail, eagle_summary, product_master) |
| app.py → lead_times | sap_df with source_country | sap_df with deadline columns added |
| app.py → merger | sap_df, tracker_df, eagle_summary_df | merged Active_PO_Control_Table DataFrame (note: 62-prefix POs excluded) |
| app.py → risk | merged_df, lead_time rules | merged_df with urgency, exceptions, owner, action |
| app.py → quality | all 4 DataFrames | Data quality log (DataFrame) |

## 5. Third-party integrations
- **None.** All data is user-uploaded Excel files. No APIs, no cloud services, no external calls.

## 6. Non-negotiables / constraints
- All data stays on the user's local machine. Zero network calls.
- No database server — SQLite or otherwise. JSON files for config.
- Single .exe distribution. No Python install required by end users.
- SAP Open-PO is the master source. Tracker and Eagle Eye enrich only.
- Lead time rules are configurable, not hardcoded.
- Different units of measure (KG, L, GEB) must never be summed together.
- POs can have multiple materials — each SAP PO-material row is preserved.
- 62-prefix POs (Aptoris-Tolling-BD) are contract manufacturing, not imports — always excluded.
- Product Master is the source of truth for AGI code → Source Country mapping.

## 7. Open questions
- Confirm the default Lead_Time_Rules for common Source Countries (India, China, Korea, Singapore, etc.).
- Product Master lead time columns (J=PO to ExW, K=Transit time, L=Total Lead Time) are empty — will the Country Manager populate these, or should we configure rules manually?
- 14 SAP materials have no matching AGI in Product Master — needs investigation.
