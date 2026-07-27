# Import Control Tower — CLAUDE.md

## Project Context
Building a local-only Import Control Tower dashboard for the Bangladesh Planning Manager. Python + Streamlit + PyInstaller. Data stays on the user's laptop. No cloud.

## Context Files (read these first in every session)
Always read these files before writing any code:

1. `context/architecture.md` — Solution design, tech stack, data flow
2. `context/phases.md` — Build phases (what to build next)
3. `context/database.md` — Data model, DataFrame schemas, JSON configs
4. `context/prompts.md` — System prompt with embedded real-file facts
5. `context/security.md` — Local-only, no cloud, no secrets
6. `context/error-handling.md` — Error types, boundaries, quality log

## Current Phase
Phase 1 — Engine (Processing Core). Building loader, merger, lead_times, risk, quality modules.

## Key Facts (from real file inspection on 27-Jul-2026)
- SAP: 155 rows, 153 POs (138 start with 65, 15 start with 62)
- Tracker: 1M+ rows, ~94% blank. Filter early. Sheet: "Tracker file" only.
- Eagle Eye: 165 rows, 103 POs. Status 1-6. Col U = "Probability of Meeting ETA" (0-1).
- Product Master: 68 products, sheet "Master". Col C = AGI code (int), Col F = Source Country.
- AGI cross-ref: SAP Material → strip leading zeros → match PM AGI. 47/61 matched, 14 unmatched.
- 62-prefix POs = "Aptoris-Tolling-BD" (contract manufacturing, always excluded)

## File Structure
```
import-control-tower/
├── app/                       # All application code
│   ├── app.py                 # Streamlit entry point
│   ├── requirements.txt
│   ├── build_exe.bat
│   ├── config/
│   │   ├── lead_time_rules.json
│   │   └── urgency_thresholds.json
│   ├── reference/
│   │   └── product_master.xlsx  # Persistent AGI → Source Country lookup
│   ├── engine/
│   │   ├── loader.py
│   │   ├── lead_times.py
│   │   ├── merger.py
│   │   ├── risk.py
│   │   └── quality.py
│   ├── ui/
│   │   ├── dashboard.py
│   │   ├── drilldown.py
│   │   ├── quality_log.py
│   │   └── config_page.py
│   └── tests/
├── context/                  # 6 context .md files (read above)
├── Files Shared With Me/     # Source Excel files, audio, Word docs
├── Power Query Learning/     # M code reference files
└── CLAUDE.md
```

## Rules
- Never propose cloud services, databases, or API integrations
- SAP Open PO is the master source — Tracker and Eagle Eye only enrich
- Never sum different units of measure (KG + L + GEB)
- Lead time rules must be configurable in JSON, not hardcoded
- All data stays on the local machine — zero network calls
