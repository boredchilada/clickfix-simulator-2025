import os
import re
from flask import Blueprint, render_template, request, redirect, url_for, abort, send_from_directory, current_app
from app.extensions import db
from app.models import Campaign, Target
from app.utils import sanitize_filename, generate_payload, log_event

lure_bp = Blueprint('lure', __name__)

# Allowlist of valid trap types to prevent SSTI via template inclusion
ALLOWED_TRAPS = frozenset({
    'cloudflare',
    'chrome_update',
    'windows_update',
    'filefix',
    'missing_font',
    'root_certificate',
    'teams_error'
})

@lure_bp.route('/s/<path:slug>')
def lure(slug):
    # Sanitize input
    safe_slug = sanitize_filename(slug)
    if safe_slug != slug:
        return abort(404)
    slug = safe_slug

    # --- ASSET RESOLUTION (Fallback) ---
    # If the slug corresponds to a file in campaigns or lures, serve it.
    # This handles cases where relative assets are requested (e.g. /s/campaign/style.css)
    lures_dir = os.path.join(current_app.root_path, '..', 'templates', 'lures')
    campaigns_dir = os.path.join(current_app.root_path, '..', 'templates', 'lures', 'scenarios')
    
    # Check if it's a file in campaigns
    if os.path.isfile(os.path.join(campaigns_dir, slug)):
        return send_from_directory(campaigns_dir, slug)
    
    # Check if it's a file in lures
    if os.path.isfile(os.path.join(lures_dir, slug)):
        return send_from_directory(lures_dir, slug)

    # --- LURE LOGIC ---
    user_id = request.args.get('uid')
    trap_type = request.args.get('t')
    
    # Validate trap_type against allowlist to prevent SSTI
    if trap_type and trap_type not in ALLOWED_TRAPS:
        trap_type = None
    
    if user_id and not re.match(r'^[a-zA-Z0-9\.\-_]+$', user_id):
        return abort(400, "Invalid User ID format")

    if not user_id:
        import uuid
        user_id = str(uuid.uuid4())[:8]
        # Preserve query parameters
        args = request.args.copy()
        args['uid'] = user_id
        return redirect(url_for('lure.lure', slug=slug, **args))

    # --- CAMPAIGN RESOLUTION LOGIC ---
    # 1. Check if this is a registered Campaign Slug
    campaign = Campaign.query.filter_by(slug=slug).first()
    scenario = None

    if campaign:
        scenario = campaign.scenario
        # Override trap_type if defined in campaign
        if campaign.trap_slug:
            trap_type = campaign.trap_slug
    else:
        # 2. Fallback: Treat slug as a scenario name (Legacy Mode)
        scenario = slug
    
    # --- TEMPLATE RESOLUTION ---
    template_to_render = None

    # Check Cloned Campaigns
    campaign_path = os.path.join(campaigns_dir, scenario)
    if os.path.isdir(campaign_path) and os.path.exists(os.path.join(campaign_path, 'index.html')):
        template_to_render = f'lures/scenarios/{scenario}/index.html'

    # Check Static Lures
    if not template_to_render:
        lure_path = os.path.join(lures_dir, scenario)
        if os.path.isdir(lure_path) and os.path.exists(os.path.join(lure_path, 'index.html')):
            template_to_render = f'lures/{scenario}/index.html'
        elif os.path.exists(f'{lure_path}.html'):
            template_to_render = f'lures/{scenario}.html'
    
    if not template_to_render:
        return abort(404)

    # --- TARGET TRACKING ---
    target = Target.query.filter_by(user_id=user_id).first()
    if not target:
        if not campaign:
            # Auto-create campaign for Legacy Mode
            campaign = Campaign.query.filter_by(scenario=scenario, slug=None).first()
            if not campaign:
                campaign = Campaign(name=f"Auto: {scenario}", scenario=scenario)
                db.session.add(campaign)
                db.session.commit()
            
        target = Target(campaign_id=campaign.id, user_id=user_id)
        db.session.add(target)
        db.session.commit()

    # Log Page View
    log_event(user_id, 'PAGE_VIEW')

    # Generate payload for this user
    # CRITICAL: Use configured SERVER_URL for cloud/proxy compatibility.
    # Fallback to request.host only if config is missing (dev mode).
    public_host = current_app.config.get('SERVER_URL') or request.host
    
    # Strip protocol if accidentally included in config
    if '://' in public_host:
        public_host = public_host.split('://')[1]
        
    server_url = f"https://{public_host}"
    payload = generate_payload(user_id, server_url)

    # Pass tracking endpoint to template for JS
    track_endpoint = current_app.config.get('ENDPOINT_TRACK', '/track/click')
    if not track_endpoint.startswith('/'): track_endpoint = '/' + track_endpoint

    return render_template(
        template_to_render,
        payload=payload,
        user_id=user_id,
        trap_type=trap_type,
        track_endpoint=track_endpoint # Pass to template
    )