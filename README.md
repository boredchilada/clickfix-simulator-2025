# ClickFix Training Tool

**A lightweight, self-hosted simulation tool for "ClickFix" type social engineering attacks.**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Docker](https://img.shields.io/badge/docker-supported-blue)

## Disclaimer

**This tool is for AUTHORIZED SECURITY AWARENESS TRAINING ONLY.**
Unauthorized use of this tool to target systems or users without explicit permission is illegal and unethical. The authors are not responsible for any misuse of this software.

## Overview

ClickFix (also known as "ClearFake" or "Fake Update") is a social engineering technique where attackers trick users into manually executing malicious commands (usually via the Windows Run dialog) to "fix" a fake error. Because the user initiates the execution, this technique often bypasses traditional security controls.

**The ClickFix Training Tool** allows security teams to simulate these attacks safely to train employees.

**Key Features:**
*   **Safe Simulation:** Uses harmless payloads (MessageBox + Redirect) instead of malware.
*   **Realistic Lures:** Includes templates for Teams, SharePoint, Cloudflare, and more.
*   **Site Cloner:** Built-in tool to clone legitimate sites and inject the trap.
*   **Tracking:** Logs page views, clicks, and payload executions.
*   **Privacy-First:** Self-hosted, no external data exfiltration.

## Quick Start

### Option A: Docker (Recommended)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/boredchilada/clickfix-simulator-2025.git
    cd clickfix-simulator-2025
    ```

2.  **Start the container:**
    ```bash
    docker-compose up -d
    ```

3.  **Access the tool:**
    *   **Admin Dashboard:** `https://localhost/admin` (User: `admin`, Pass: `changeme_please`)
    *   **Test Lure:** `https://localhost/s/teams_error?uid=test_user`

### Option B: Local Python Setup

1.  **Prerequisites:** Python 3.8+, `pip`, `openssl` (for certs).

2.  **Install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```

3.  **Initialize Database:**
    ```bash
    flask init-db
    ```

4.  **Generate Certificates (Required for Clipboard API):**
    ```bash
    mkdir certs
    openssl req -x509 -newkey rsa:4096 -nodes -keyout certs/key.pem -out certs/cert.pem -days 365 -subj "/CN=localhost"
    ```

5.  **Run the server:**
    ```bash
    python run.py
    ```

## Architecture

The tool is built with **Flask** (Python) and uses **SQLite** for data storage.

*   **`run.py`**: Main application logic, routes, and payload generation.
*   **`cloner.py`**: Utility to clone websites and inject traps.
*   **`templates/`**:
    *   `lures/`: Full-page attack templates.
    *   `traps/`: HTML fragments (popups/overlays) injected into cloned sites.
    *   `scenarios/`: Storage for cloned sites.
*   **`static/`**: CSS, JS, and images.

## Advanced Configuration

### Webhook Notifications
To receive real-time alerts when a user clicks the fix button or executes the payload, set the `WEBHOOK_URL` environment variable.
Supported formats: Slack, Discord, Microsoft Teams (Incoming Webhook).

```yaml
environment:
  - WEBHOOK_URL=https://hooks.slack.com/services/T000/B000/XXXX
```

### Dynamic Trap Selection
You can override the default trap for any campaign by appending `?t=<trap_name>` to the URL.
Example: `https://training.local/s/teams_error?uid=john&t=cloudflare`

### Database Scalability
By default, the tool uses SQLite (`training_log.db`). For high-volume campaigns or load-balanced deployments, you can switch to PostgreSQL or MySQL by setting `SQLALCHEMY_DATABASE_URI`.

```yaml
environment:
  - SQLALCHEMY_DATABASE_URI=postgresql://user:pass@db_host:5432/clickfix
```

## Security Considerations

*   **HTTPS is Mandatory:** The `navigator.clipboard.writeText()` API requires a Secure Context (HTTPS or localhost). The tool will not work over plain HTTP on a network.
*   **Payload Safety:** The default payload only opens a message box and redirects the browser. It does not execute any system changes.
*   **Access Control:** The Admin Dashboard is protected by Basic Auth. Change the default credentials in `docker-compose.yml` or `.env` before deployment.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Roadmap

### v1.0 (Current) - Training Mode
- ✅ Core ClickFix simulation
- ✅ 3 trap templates (Cloudflare, Chrome, Windows Update)
- ✅ Full event tracking and admin dashboard
- ✅ Simple site cloner with trap injection

### v1.1 - Enhanced Payloads
- [ ] Multiple payload types (MSHTA, LOLBins)
- [ ] Basic obfuscation options
- [ ] macOS/Linux execution triggers

### v1.2 - Configuration System
- [ ] YAML-driven campaign configuration
- [ ] Dynamic branding engine
- [ ] Custom trap templates

### v2.0 - Red Team Mode
- [ ] Bot/crawler detection
- [ ] Geofencing and IP targeting
- [ ] DNS callback verification
- [ ] Time-based campaign controls

## Known Limitations (v1.0)

1. **Windows-Only Instructions**: The execution triggers (Win+R) are Windows-specific. macOS/Linux support planned for v1.1.
2. **Single Payload Type**: Only PowerShell IEX stager is supported. Additional payload types planned for v1.1.
3. **No Evasion Features**: Bot detection and geofencing are not implemented. Planned for v2.0.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.