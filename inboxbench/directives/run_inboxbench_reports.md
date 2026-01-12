# Directive: Run InboxBench Daily Reports

**Goal**: Automate the generation of daily email deliverability and campaign performance reports for "InboxBench" clients, updating a specific Google Sheet for each client and sending a consolidated email summary to the admin.

## 1. System Architecture
-   **Source**: Instantly.ai API V2 (Campaigns, Accounts, Analytics).
-   **Filter**: Clients are identified by **Tags** in Instantly.
-   **Storage**: One Google Sheet per Client (Overview, Campaign Performance, Account Health).
-   **Notification**: Consolidated Email Summary via Resend API.

## 2. Configuration (`config/config.json`)

```json
{
    "instantly_api_key": "YOUR_INSTANTLY_API_KEY_BASE64",
    "resend_api_key": "YOUR_RESEND_API_KEY",
    "agency_name": "Sipes Automation",
    "reporting_email": "msipes@sipesautomation.com",
    "client_profiles": [
        {
            "tag_name": "Sipes Automation",
            "client_name": "Sipes Automation (Internal)",
            "google_sheet_id": "1qdWFdxmm8M8WlbrWZgLP5REI_pxwp_dq1MXWiwMFizw"
        }
    ]
}
```

## 3. SOP: Adding a New Client
1.  **Instantly Setup**:
    -   Create a **Tag** for the client (e.g., "Client X").
    -   Tag all relevant Campaigns and Email Accounts with this tag.
2.  **Google Sheet Setup**:
    -   Create a new Google Sheet (or duplicate the template).
    -   **Important**: Share the sheet with the Service Account as **Editor**:
        `antigravity@antigravity-479502.iam.gserviceaccount.com`
    -   Copy the **Spreadsheet ID** from the URL.
3.  **Update Config**:
    -   Add a new object to `client_profiles` in `config.json` with the `tag_name`, `client_name`, and `google_sheet_id`.

## 4. Execution
Run the orchestrator script (daily cron or manual):

```bash
python3 inboxbench/orchestration/main_workflow.py
```

## 5. Troubleshooting
### Permission Denied (403) for Google Sheets
-   **Cause**: The Google Sheets API is not enabled for the project OR the specific sheet is not shared with the service account.
-   **Fix**:
    1.  Ensure API is enabled: [Enable Link](https://console.cloud.google.com/apis/library/sheets.googleapis.com?project=antigravity-479502)
    2.  Check the sheet's "Share" settings contain the service account email.

### Tag Not Found / Empty Data
-   **Cause**: Tag name mismatch or no items tagged.
-   **Fix**: Verify the tag name in `config.json` matches Instantly *exactly* (case-sensitive) and that campaigns/accounts are actually tagged.

### Import Errors
-   **Cause**: Running scripts from the wrong directory.
-   **Fix**: Always run from the project root (`inboxbench/` parent) or ensure `PYTHONPATH` includes the workspace. The scripts append paths relative to `__file__`, so running from `inboxbench/` root is best.
