# Phases

> Build phases for the Import Control Tower. Each phase must be usable on its own.

## Phase 1 — Engine (Processing Core)
**Goal:** The data processing pipeline works correctly. Can be verified with sample data.

- [ ] **loader.py** — Read/normalize all 4 Excel files (SAP, Tracker, Eagle Eye, Product Master). Cross-ref SAP Material → PM AGI → Source Country. Extract 10-digit PO keys. Exclude 62-prefix POs. Parse dates. Generate eagle_detail + eagle_summary aggregations.
- [ ] **lead_times.py** — Load configurable Lead_Time_Rules from JSON. Resolve by precedence (Material+Route → Material → Route → Default → Data Review).
- [ ] **merger.py** — SAP-first LEFT JOIN onto Tracker and Eagle Eye. Generate Data_Visibility_Status. (Scope_Mapping removed — 62-prefix hard-excluded in loader.)
- [ ] **risk.py** — Evaluate 6 exception types. Assign Primary Exception, All Exceptions, Urgency, Recommended Owner, Next Action.
- [ ] **quality.py** — Build data quality log (orphan records, date conflicts, missing rules, invalid PO keys).
- [ ] **Unit tests** — test_loader, test_merger, test_lead_times, test_risk, test_quality.

**Done when:** All 5 engine modules pass tests. Processing the 3 sample files produces correct output.

**Architecture touched:** `engine/` (loader, lead_times, merger, risk, quality), `config/` (lead_time_rules.json)

## Phase 2 — UI (Dashboard)
**Goal:** The Planning Manager can upload files and see results in a browser.

- [ ] **app.py** — Streamlit entry point. File upload page with drag-and-drop for SAP, Tracker, Eagle Eye (Product Master is a one-time reference, re-uploadable via admin).
- [ ] **Executive Dashboard** — Summary metric cards (total POs, critical/urgent counts, open qty). Exception breakdown bar chart (Plotly). Visibility status counts.
- [ ] **Prioritised Action List** — Full table sorted by urgency. Colour-coded rows. Default filter: Critical + Urgent. Search/filter by PO, product, supplier. Excel download button.
- [ ] **PO Drill-Down** — Expandable detail section. Process timeline (SAP open → LC → SI → ETD → ETA → OBL/EBL → Final Docs). Container-level Eagle Eye details. All exceptions for this PO.
- [ ] **Data Quality Log tab** — All data issues tabulated with severity.
- [ ] **Configuration page** — Edit Lead_Time_Rules (add/delete rows). Re-upload Product Master. Changes saved to JSON/Excel files.

**Done when:** A user can upload files, see the dashboard, filter/sort, drill into a PO, inspect data quality issues, and edit rules.

**Architecture touched:** `ui/` (dashboard, drilldown, quality_log, config_page), `app.py`

## Phase 3 — Packaging & Distribution
**Goal:** The app ships as a single .exe. Team members can run it without Python.

- [ ] **PyInstaller build** — Package with `--onefile --windowed`. Streamlit auto-launches browser on start.
- [ ] **build_exe.bat** — One-click build script.
- [ ] **Test on clean Windows machine** — Verify .exe works with no Python installed. Upload real files, confirm all features work.
- [ ] **Distribution** — Share .exe via OneDrive. 4 team members each run their own copy.

**Done when:** The .exe file is built, tested on a clean machine, and shared with the team.

**Architecture touched:** `build_exe.bat`, `dist/ImportControlTower.exe`

## Phase 4 — Polish
**Goal:** Production-ready quality.

- [ ] **Empty states** — Handle no files uploaded, no matching data, all POs on track.
- [ ] **Loading states** — Progress indicators during file processing.
- [ ] **Error boundaries** — Graceful error messages for invalid files, corrupt data, unexpected formats.
- [ ] **Streamlit session state** — Persist dashboard state across reruns so filters survive interactions.
- [ ] **Sample data** — Include sample Excel files in the distribution for testing.
- [ ] **User guide** — Brief README or in-app instructions.

**Done when:** The app handles all edge cases gracefully and is ready for daily use.

**Architecture touched:** `ui/` error handling, `sample_data/`

## Backlog (not scheduled yet)
- Email draft alerts (generate text, don't send)
- Historical trend tracking (exception patterns over time)
- SAP API integration (automated PO refresh)
- Multi-user deployment with shared state
- Automated scheduling (cron-based refresh)
