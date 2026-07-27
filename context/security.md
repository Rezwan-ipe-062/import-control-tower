# Security

> Security practices for the Import Control Tower. This is a local-only desktop app with no network calls and no user accounts.

## Authentication
- [ ] **No user authentication required.** The app runs on localhost and is accessed only by the person running it on their own machine.
- [ ] The .exe runs on the user's local PC. No shared server, no multi-tenancy.

## Authorization
- [ ] **Not applicable.** Single-user app. The user has full access to their own data.
- [ ] No role system, no row-level security.

## Data handling
- [x] **All data stays on the local machine.** The app reads Excel files from the user's file system via Streamlit's file uploader or local path. Nothing is sent over the network.
- [x] **No cloud services.** No external API calls, no database server, no telemetry to external servers.
- [x] **No persistent storage of source data.** The uploaded Excel files are only held in memory during the Streamlit session. When the app closes, all data is gone.
- [x] **JSON config files (lead_time_rules, scope_mapping) are stored locally only.** No sync, no backup to cloud.

## Input validation
- [ ] **File validation at upload** — Verify uploaded files are valid .xlsx format before attempting to read.
- [ ] **Column presence check** — Verify required columns exist before processing. Show clear error if a file is missing expected columns.
- [ ] **Date parsing** — Handle invalid dates gracefully (log a data quality warning, don't crash).
- [ ] **PO key validation** — Verify a 10-digit PO number can be extracted. Flag rows where it can't.

## Secrets & config
- [x] **No secrets used.** The app has no API keys, no passwords, no database credentials.
- [x] `.env` files not needed. No secrets to manage.
- [ ] Config files (JSON) are separated from code in `config/` directory.

## Transport & headers
- [x] **Not applicable.** No network services. Streamlit runs on localhost only.

## File system
- [ ] The app reads and writes only:
  - User-provided Excel files (read-only, in-memory)
  - `config/lead_time_rules.json` (read/write via config page)
  - `config/scope_mapping.json` (read/write via config page)
- [ ] The app never accesses system files, other user documents, or network locations.

## PyInstaller packaging
- [ ] Verify the packaged .exe has no debug symbols or development paths embedded.
- [ ] Run `pyinstaller --noconfirm --clean` to avoid caching issues.
- [ ] Verify the .exe doesn't trigger false antivirus alerts (common with PyInstaller — sign with a certificate if needed).

## Pre-launch checklist
- [ ] No network calls in the code (grep for `http://`, `https://`, `requests.`, `urllib.`)
- [ ] No secrets or credentials in the codebase
- [ ] No debug/verbose errors leaked to end users (see error-handling.md)
- [ ] File upload validation works for all 3 file types
- [ ] .exe builds cleanly on a fresh Windows machine
- [ ] App works with no internet connection (fully offline)
