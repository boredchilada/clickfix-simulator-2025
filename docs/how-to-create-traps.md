# How to Create Custom Traps

This guide explains how to create new "Traps" for the ClickFix Training Tool. A trap is the UI element (like a popup or overlay) that tricks the user into copying the payload to their clipboard.

## Overview

Traps are HTML fragments located in `templates/traps/`. They are injected into Lures or Cloned Campaigns.

A trap consists of:
1.  **HTML Structure:** The visual design of the popup/overlay.
2.  **CSS Styling:** To make it look realistic (often mimicking system dialogs).
3.  **JavaScript Trigger:** A specific function call to `ClickFix.trigger()` which handles the clipboard injection.

## Step-by-Step Guide

### 1. Create the File

Create a new HTML file in `templates/traps/`. For this example, we'll create a "Browser Update" trap.

**File:** `templates/traps/browser_update.html`

### 2. Add the HTML Structure

The HTML should be self-contained. You can use inline CSS or add styles to `static/css/styles.css` (though inline/scoped is better for portability).

```html
<!-- Browser Update Trap -->
<div id="browser-update-overlay" style="
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.8);
    z-index: 9999;
    display: flex;
    justify-content: center;
    align-items: center;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
">
    <div style="
        background: white;
        padding: 20px;
        border-radius: 8px;
        width: 400px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    ">
        <h2 style="color: #d93025; margin-top: 0;">Critical Update Required</h2>
        <p style="color: #333; margin: 15px 0;">
            Your browser is out of date and missing critical security patches. 
            Please update immediately to continue browsing safely.
        </p>
        
        <div style="margin-top: 20px;">
            <button id="update-btn" style="
                background: #1a73e8;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 4px;
                font-size: 14px;
                cursor: pointer;
                font-weight: 500;
            ">
                Update Now
            </button>
        </div>
    </div>
</div>
```

### 3. Add the JavaScript Trigger

We provide a shared utility `ClickFix.trigger()` (available globally) to handle the core logic (Clipboard + Tracking). You just need to provide the callback for your UI changes.

Add this script block to the bottom of your file. We recommend defining a function and calling it via `onclick` in your HTML.

```html
<script>
    function triggerTrap() {
        // Get variables injected by Flask
        const payload = `{{ payload|safe }}`;
        const userId = "{{ user_id }}";
        const trackEndpoint = "{{ track_endpoint|default('/track/click') }}";

        // Trigger the attack sequence
        ClickFix.trigger(payload, userId, trackEndpoint, function() {
            // --- SUCCESS CALLBACK ---
            // This runs after the payload is successfully copied.
            // Use this to show your instruction overlay or start an animation.
            
            console.log("Trap triggered successfully!");
            
            // Example: Show a hidden overlay
            // document.getElementById('browser-update-overlay').style.display = 'none'; // Optional: Hide initial trap
            document.getElementById('instruction-overlay').style.display = 'flex'; // Show instructions
            
        }, function(error) {
            // --- ERROR CALLBACK ---
            // Runs if clipboard access fails (e.g., non-HTTPS)
            console.error("Trap failed:", error);
            alert("Error: Clipboard access denied. Ensure you are using HTTPS.");
        });
    }
</script>
```

Then, update your button to call this function:

```html
<button id="update-btn" onclick="triggerTrap()" style="...">
    Update Now
</button>
```

### 4. Testing Your Trap

To test your new trap, you can use the Site Cloner or manually create a Lure.

**Option A: Using URL Parameter (Quickest)**
If you have a running instance, you can force any campaign to use your new trap by adding `?t=browser_update` to the URL.

Example: `https://localhost/s/teams_error?t=browser_update`

**Option B: Using the Cloner**
You can now use this trap when cloning a site:

```bash
python cloner.py https://example.com my_campaign --trap browser_update
```

**Note:** You must update `cloner.py` to include your new trap in the `choices` list if you want it to be selectable via the CLI.

## Best Practices

*   **Realism:** Use screenshots or exact color codes from the software you are mimicking.
*   **Urgency:** The text should create a sense of urgency (e.g., "Security Error", "Missing Font", "Update Required").
*   **Isolation:** Try to keep your CSS styles specific to your elements to avoid breaking the layout of the cloned site. Using unique IDs or a shadow DOM approach (advanced) is recommended.
*   **Responsiveness:** Ensure your overlay works on different screen sizes, although these attacks are primarily targeted at Desktop users (since the PowerShell payload is Windows-specific).

## Advanced: Dynamic Content

You can use Jinja2 syntax in your trap file if you need dynamic data, as it is rendered by Flask.

```html
<p>Hello, {{ request.args.get('uid', 'User') }}</p>