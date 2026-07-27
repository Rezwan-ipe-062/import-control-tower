# Error Handling

> How errors are caught, classified, and displayed. This is a local desktop app — errors surface as Streamlit UI messages, not HTTP responses.

## Principles
- Never crash on bad data — log the issue in the Data Quality Log and continue.
- Show human-readable error messages in the UI (no stack traces).
- Every error has: a **type**, a **user-friendly message**, and a **log entry**.
- Data quality issues are warnings, not errors — they go in the quality log, not as crash blockers.

## Error types

| Type | When | UI Behaviour |
|------|------|-------------|
| File Validation Error | Uploaded file is not a valid .xlsx, wrong sheet names, missing columns | Show error message on the upload page. Stop processing. |
| Date Parsing Warning | A date value can't be parsed (invalid format, garbage text) | Log in Data Quality Log. Set date to null. Continue processing. |
| PO Key Warning | Can't extract a 10-digit normalized PO from a row | Log in Data Quality Log. Skip that row from merge but keep in source view. |
| Missing Lead Time Rule | No matching rule found for a PO's material/route | Log in Data Quality Log. Set urgency to "Data Review". Continue processing. |
| File Read Error | File is corrupt, password protected, or empty | Show error message. Ask user to re-upload. |
| Unexpected Error | Any unhandled exception during processing | Streamlit shows error boundary. Log full traceback to console. Show generic message to user. |

## Streamlit error boundaries

**File upload page:**
- Invalid file type → `st.error("The file must be an .xlsx workbook.")`
- Missing sheet → `st.error("Could not find sheet '{sheet_name}' in {filename}. Expected sheets: Open PO, Tracker file, Sheet1, Master.")`
- Empty file → `st.warning("{filename} contains no data rows. Please check the file.")`

**Processing pipeline:**
- Each engine module is wrapped in try/except that sets error state rather than halting
- If loader fails → display the error, don't proceed to dashboard
- If merger finds no matching data → `st.info("No SAP POs matched Tracker or Eagle Eye records.")`
- If lead_times has no rules configured → `st.warning("No lead time rules configured. Add rules in the Configuration tab.")`

**Dashboard:**
- Empty DataFrames → show `st.info("No POs match the current filter.")` with guidance
- Vizualization errors → fall back to plain table, log the error

## Standard error display format
```
Error: [type]
What happened: [plain English description of what went wrong]
What to do: [action the user should take to fix it]
```

Example:
```
Error: File Validation
What happened: The file "BD_TRACKER.xlsx" doesn't contain a "Tracker file" sheet. Found sheets: Sheet1, Completed, Cancelled PO.
What to do: Upload the correct BD Tracker file with a sheet named "Tracker file".
```

## Data Quality Log (not errors, but surfaced to user)
The Data Quality Log is the canonical place for warnings about data consistency:

| Issue | Example |
|---|---|
| SAP PO not in Tracker | "PO 6590029002 has no Tracker record" |
| SAP PO not in Eagle Eye | "PO 6590028665 has no Eagle Eye shipment visibility" |
| SAP PO in neither source | "PO 6590028959 is invisible in both Tracker and Eagle Eye" |
| Orphan Tracker record | "Tracker PO 6590028230 has no matching open SAP PO" |
| Orphan Eagle Eye record | "Eagle Eye PO 6590028423 has no matching open SAP PO" |
| Date conflict | "SAP Delivery Date (01-Aug-2026) differs from Tracker RDD (15-Aug-2026)" |
| No lead time rule | "No lead time rule found for Source Country 'Syngenta, India'." |
| AGI code mismatch | "SAP Material '0093171' has no matching AGI code in Product Master." |
| Multiple containers | "PO 6590027103 has 3 containers" |

## Logging
- Log level: ERROR for processing failures, WARNING for data quality issues, INFO for uploads and processing completion.
- Log destination: Streamlit console (visible during development) + optional sidebar expander ("Processing Log") for end users.
- Log format per entry: `[timestamp] [LEVEL] [module] message`

## What NEVER reaches the user
- Python stack traces (caught by Streamlit's default error handler, but we override with friendly messages)
- Pandas warnings about downcasting, SettingWithCopy, or FutureWarning
- Internal file paths from the developer's machine
- openpyxl warnings about data validation or styles
