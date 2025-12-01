# Admin Guide: Managing Campaigns

This guide covers the administration of the ClickFix Training Tool, including creating campaigns, monitoring results, and interpreting data.

## Accessing the Dashboard

The Admin Dashboard is located at `/admin`.
*   **URL:** `https://your-domain.com/admin`
*   **Default Credentials:**
    *   Username: `admin`
    *   Password: `changeme_please` (Change this in `.env` or `docker-compose.yml`!)

## Dashboard Overview

The main dashboard provides a high-level view of your training program:
*   **Total Campaigns:** Number of active and inactive campaigns.
*   **Total Targets:** Number of unique users tracked.
*   **Total Events:** Total number of interactions logged.
*   **Recent Events:** A live feed of the latest clicks and executions.

## Creating a Campaign

1.  Navigate to the **Campaigns** section.
2.  Click **"Create New Campaign"**.
3.  Fill in the details:
    *   **Name:** Internal name for the campaign (e.g., "Q3 Finance Phishing").
    *   **Client:** (Optional) Name of the department or client being tested.
    *   **Slug:** The URL path for the campaign (e.g., `finance-update`). The full link will be `https://domain.com/s/finance-update`.
    *   **Scenario:** Choose the base template.
        *   *Lure:* A static page (e.g., Teams Error).
        *   *Cloned Site:* A site you created with the Cloner tool.
    *   **Trap:** (Optional) Override the default trap for this campaign.
4.  Click **Create**.

## Monitoring a Campaign

Click on a campaign name to view its specific dashboard.

### Metrics
*   **Views:** How many times the page was loaded.
*   **Clicks:** How many users clicked the "Fix" button (fell for the lure).
*   **Executions:** How many users actually ran the PowerShell command (full compromise).

### Event Log
A detailed table showing every interaction:
*   **Time:** Timestamp of the event.
*   **User ID:** The unique ID of the target.
*   **Event:** `PAGE_VIEW`, `BUTTON_CLICK`, `PAYLOAD_EXECUTED`, or Training Events (`TRAINING_VIEWED`, `TRAINING_COMPLETED`, `TRAINING_ACKNOWLEDGED`).
*   **Details:** IP address, User Agent, and (for executions) Hostname/Username.

## Exporting Data

You can export all event data to a CSV file for reporting or external analysis.
1.  Go to the main Admin Dashboard.
2.  Click the **"Export CSV"** button in the top right.

## Webhook Notifications

For real-time monitoring, you can configure a webhook (Slack, Discord, Teams).
*   **Setup:** Set the `WEBHOOK_URL` environment variable.
*   **Triggers:** You will receive a notification for every `BUTTON_CLICK` and `PAYLOAD_EXECUTED`.

## User Management

The tool uses a "Target" model to track users.
*   **UID:** Users are identified by a `uid` parameter in the URL (e.g., `?uid=john.doe`).
*   **Auto-Creation:** If a user visits a link with a new `uid`, a Target record is automatically created.
*   **Anonymous:** If no `uid` is provided, the system generates a random ID, but you won't be able to attribute it to a specific employee.

**Best Practice:** When distributing links via email using a phishing simulation platform (like GoPhish) or an email marketing tool, use their variable syntax to dynamically insert the user's email.

*   **GoPhish Example:** `https://training.local/s/campaign?uid={{.Email}}`
*   **Mailchimp Example:** `https://training.local/s/campaign?uid=*|EMAIL|*`
*   **Manual:** `https://training.local/s/campaign?uid=john.doe@example.com`