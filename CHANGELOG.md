# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-11-30

### Added
- **Modular Architecture**: Refactored monolithic `app.py` into a scalable Flask Blueprint structure (`app/blueprints/`).
- **Database Models**: Implemented SQLAlchemy models (`Campaign`, `Target`, `Event`) for structured data persistence.
- **Advanced Event Tracking**: Enhanced `Event` model to capture `source_ip`, `hostname`, `username`, `user_agent`, and `platform`.
- **Interactive Timeline**: Added `static/js/timeline.js` and `static/css/timeline.css` to power a new interactive dashboard chart with filtering, drill-down capabilities, and API integration.
- **Timeline Filtering System**: Implemented two-level filtering with bidirectional sync between Event Type Chips (API data control) and Legend Items (visual control), with smooth segment animations.
- **Global ClickFix Utility**: Refactored core attack logic into `static/js/clickfix.js`, exposing a global `ClickFix` object for standardized clipboard manipulation, fallback handling, and progress simulation across all templates.
- **UI Utilities Library**: Created `static/js/ui.js` providing modern replacements for native browser dialogs:
  - Toast notifications (info, success, warning, error) with slide-in animations
  - Styled modal confirmations with backdrop blur
  - Form submission helpers
- **Admin Navigation Dock**: Implemented floating macOS-style navigation (`templates/components/admin_nav.html`) with:
  - Quick campaign switcher with popover menu
  - Minimize/restore functionality with localStorage persistence
  - Context-aware buttons (e.g., export current campaign vs all data)
  - Smooth elastic animations and responsive design
- **Training Module Enhancements**: Added `static/css/training.css` with full-screen scroll-snap sections, fade-in animations, and responsive layouts.
- **Proxy Support**: Integrated `werkzeug.middleware.proxy_fix` for accurate IP resolution behind load balancers.
- **Concurrency**: Enabled SQLite Write-Ahead Logging (WAL) mode for improved database performance.
- **New Lure Templates**: Added `outlook_attachment`, `pdf_viewer`, `sharepoint_document`, `video_player`, and `vpn_connection`.
- **New Trap Templates**:
  - `windows_update` - Fullscreen trap with realistic progress animation
  - `missing_font` - Font installation trap
  - `root_certificate` - Browser security warning trap
- **Documentation**: Added comprehensive guides in `docs/` (`admin-guide.md`, `deployment-guide.md`, `technical-architecture.md`).
- **Testing Utilities**: Added `test-docker.bat` and `test-docker-compose.bat` for automated deployment verification.
- **Stealth Routes**: Dynamic route registration in `app/blueprints/stealth.py` for configurable payload endpoints.
- **Interactive Training**: Enhanced `static/js/training.js` with IntersectionObserver-based animations and scroll tracking.

### Changed
- **Configuration**: Centralized configuration in `config.py` with environment variable overrides.
- **Admin Dashboard**: Completely rewritten to support new Campaign model, dynamic scenario selection, and the new timeline visualization.
- **User Notifications**: Replaced all native browser `alert()` and `confirm()` dialogs with custom styled components from `ClickFixUI`.
- **CSV Export**: Enhanced with context-aware filename generation (campaign-specific, client-specific, or all events).
- **Color Accessibility**: Updated CSS variables to use more accessible contrasts (e.g., Emerald 600, Red 600, Amber 700) for better WCAG compliance.
- **Dependencies**: Updated all core packages to latest versions (Flask 3.1.2, SQLAlchemy 2.0.44, requests 2.32.5) and added 40+ production-ready dependencies including testing (pytest, locust), WebSocket support (python-socketio), and monitoring (psutil).
- **File Structure**: Moved scenarios to `templates/lures/scenarios` (formerly `templates/campaigns`).
- **Entry Point**: Changed application entry point to `run.py`.
- **Cloner Utility**: Extended to support two additional trap types (`missing_font`, `root_certificate`).

### Improved
- **Dashboard UX**: Timeline chart now features synchronized two-level filtering with visual feedback and smooth animations.
- **Visual Polish**: Added elastic animations throughout the admin interface using cubic-bezier easing functions for nicer feel.
- **Mobile Responsiveness**: Enhanced mobile support for admin dock navigation and training module.
- **Accessibility**: Improved color contrast across all UI components for better WCAG compliance.
- **Developer Documentation**: Expanded [`DEVELOPER_HANDBOOK.md`](DEVELOPER_HANDBOOK.md) with detailed descriptions of timeline filtering system, UI utilities, and admin navigation components.

### Removed
- **Legacy Code**: Deleted `app.py` and `gen_payload.py` in favor of the new application factory pattern.
- **Native Browser Dialogs**: Removed all `alert()` and `confirm()` calls in favor of custom styled components.

## [1.0.0] - 2025-11-29

### Added
- Core ClickFix simulation engine with clipboard manipulation.
- Three trap templates: Cloudflare, Chrome Update, and Windows Update.
- Admin dashboard for campaign management and event tracking.
- Site cloner utility (`cloner.py`) for creating custom lures.
- Docker support with `docker-compose`.
- Webhook integration for real-time alerts (Slack, Discord, Teams).
- Configurable stealth endpoints for payload delivery.
- Training landing page with educational content.
- Clipboard fallback mechanism for older browsers.
- Platform detection warning for non-Windows users.

### Security
- Input sanitization for all file paths and slugs.
- Basic Auth protection for admin routes.
- Safe payload generation (MessageBox + Redirect only).