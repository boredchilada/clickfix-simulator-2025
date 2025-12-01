import os
from flask import Blueprint, render_template, current_app
from app.models import Campaign
from app.utils import requires_auth, log_event

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@requires_auth
def index():
    # List all available lures in the templates/lures directory
    lures_dir = os.path.join(current_app.root_path, '..', 'templates', 'lures')
    campaigns_dir = os.path.join(current_app.root_path, '..', 'templates', 'lures', 'scenarios')
    traps_dir = os.path.join(current_app.root_path, '..', 'templates', 'traps')
    
    lures = []
    campaigns = []
    traps = []

    # List Lures (Static Templates)
    if os.path.exists(lures_dir):
        for entry in os.listdir(lures_dir):
            full_path = os.path.join(lures_dir, entry)
            if os.path.isfile(full_path) and entry.endswith('.html'):
                lures.append(entry.replace('.html', ''))
            elif os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, 'index.html')):
                lures.append(entry)

    # List Campaigns (Cloned Sites)
    if os.path.exists(campaigns_dir):
        for entry in os.listdir(campaigns_dir):
            full_path = os.path.join(campaigns_dir, entry)
            if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, 'index.html')):
                campaigns.append(entry)

    # List Traps
    if os.path.exists(traps_dir):
        for entry in os.listdir(traps_dir):
            if entry.endswith('.html'):
                traps.append(entry.replace('.html', ''))
    
    # Fetch DB campaigns for the navigation menu
    all_campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    
    return render_template('index.html', lures=lures, campaigns=campaigns, traps=traps, all_campaigns=all_campaigns)

@main_bp.route('/training')
@main_bp.route('/training/<user_id>')
def training_landing(user_id=None):
    if user_id:
        log_event(user_id, 'TRAINING_VIEWED')
    return render_template('training/landing.html', user_id=user_id)