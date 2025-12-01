# How to Use the Site Cloner

The Site Cloner (`cloner.py`) is a powerful utility included with the ClickFix Training Tool. It allows you to create realistic phishing scenarios by cloning legitimate websites and injecting the ClickFix trap logic.

## Prerequisites

*   Python 3.8+ installed
*   Dependencies installed (`pip install -r requirements.txt`)
*   Internet connection (to fetch the target site)

## Basic Usage

The basic syntax is:

```bash
python cloner.py <URL> <CAMPAIGN_NAME>
```

*   **URL:** The full URL of the website you want to clone (e.g., `https://login.microsoftonline.com`).
*   **CAMPAIGN_NAME:** The name of the folder to be created in `templates/campaigns/`. This will also be the slug for the URL (e.g., `/s/my_campaign`).

**Example:**

```bash
python cloner.py https://www.google.com google_test
```

This will:
1.  Download the HTML from Google.
2.  Rewrite relative links (images, CSS, scripts) to absolute URLs pointing to Google (so the site looks correct without downloading all assets).
3.  Inject the default trap (`cloudflare`) into the page.
4.  Save the result to `templates/campaigns/google_test/index.html`.

You can now access it at: `https://localhost/s/google_test`

## Selecting a Trap

By default, the cloner injects the `cloudflare` trap. You can specify a different trap using the `--trap` argument.

**Syntax:**

```bash
python cloner.py <URL> <CAMPAIGN_NAME> --trap <TRAP_TYPE>
```

**Available Trap Types:**

*   `cloudflare` (Default): A fake Cloudflare "Verify you are human" CAPTCHA.
*   `chrome_update`: A fake Google Chrome "Critical Security Update" dialog.
*   `teams_error`: A fake Microsoft Teams "Connection Failed" error.
*   `windows_update`: A fullscreen fake Windows Update screen.
*   `filefix`: A fake "File Access Verification" overlay that tricks users into pasting into the Explorer address bar.
*   `missing_font`: A fake "User Font Pack Manager" dialog.
*   `root_certificate`: A fake "Connection Not Private" error.

**Example:**

```bash
python cloner.py https://www.cnn.com news_update --trap chrome_update
```

## How It Works

The cloner uses the `BeautifulSoup` library to parse the HTML of the target site.

1.  **Fetching:** It sends a GET request to the target URL with a standard User-Agent string.
2.  **Link Rewriting:** It iterates through all `<img>`, `<link>`, and `<script>` tags. If they use relative paths (e.g., `/static/style.css`), it converts them to absolute paths (e.g., `https://target-site.com/static/style.css`). This ensures the cloned page renders correctly without needing to host the assets locally.
3.  **Injection:** It appends a Jinja2 `{% include %}` block just before the closing `</body>` tag. This block dynamically loads the selected trap template when the page is served by Flask.

## Troubleshooting

### The cloned site looks broken
*   **CSP (Content Security Policy):** Some modern websites use strict CSP headers that prevent their assets from being loaded on other domains. The cloner cannot easily bypass this for assets loaded by the browser.
*   **JavaScript Rendering:** The cloner fetches the *initial* HTML returned by the server. It does not execute JavaScript. If the target site is a Single Page Application (SPA) built entirely with React/Vue/Angular that renders content client-side, the cloned HTML might be empty. **Solution:** Try cloning a simpler page or a specific login page that renders server-side.

### The trap isn't appearing
*   Check the source code of the cloned page (`templates/campaigns/<name>/index.html`). Look for the `{% include ... %}` block at the bottom.
*   Ensure the site doesn't have a `z-index` on its main content that is higher than the trap's `z-index`.

