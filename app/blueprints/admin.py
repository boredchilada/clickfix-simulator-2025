import datetime
import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, abort, Response, jsonify
from sqlalchemy import func, and_
from app.extensions import db
from app.models import Campaign, Event, Target
from app.utils import requires_auth, sanitize_filename, get_scenarios_and_traps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.context_processor
def inject_campaigns():
    # Only fetch if user is authenticated to avoid overhead (though requires_auth protects routes)
    # Since we can't easily check auth inside context_processor without request context issues sometimes,
    # we'll just fetch. It's safe because the templates are only rendered on protected routes.
    try:
        all_campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    except Exception:
        all_campaigns = []
    return dict(all_campaigns=all_campaigns)

@admin_bp.route('')
@requires_auth
def admin_dashboard():
    client_filter = request.args.get('client')
    
    event_query = Event.query
    campaign_query = Campaign.query

    if client_filter:
        campaign_ids = [c.id for c in Campaign.query.filter_by(client_name=client_filter).all()]
        event_query = event_query.filter(Event.campaign_id.in_(campaign_ids))
        campaign_query = campaign_query.filter_by(client_name=client_filter)

    # Fetch stats
    total_views = event_query.filter_by(event_type='PAGE_VIEW').count()
    total_clicks = event_query.filter_by(event_type='BUTTON_CLICK').count()
    total_executions = event_query.filter_by(event_type='PAYLOAD_EXECUTED').count()
    total_training_completed = event_query.filter(Event.event_type.in_(['TRAINING_COMPLETED', 'TRAINING_ACKNOWLEDGED'])).count()
    
    stats = {
        'total_views': total_views,
        'total_clicks': total_clicks,
        'total_executions': total_executions,
        'total_training_completed': total_training_completed
    }
    
    events = event_query.order_by(Event.timestamp.desc()).limit(50).all()
    
    campaigns = campaign_query.order_by(Campaign.name).all()
    
    # Get all unique client names for the filter dropdown
    clients = db.session.query(Campaign.client_name).distinct().all()
    client_names = [c[0] for c in clients if c[0]]

    scenarios, traps = get_scenarios_and_traps()
    
    return render_template('admin/dashboard.html', stats=stats, events=events, campaigns=campaigns, clients=client_names, current_client=client_filter, scenarios=scenarios, traps=traps)

@admin_bp.route('/campaign/<int:campaign_id>')
@requires_auth
def campaign_dashboard(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Funnel stats for this campaign
    views = Event.query.filter_by(campaign_id=campaign.id, event_type='PAGE_VIEW').count()
    clicks = Event.query.filter_by(campaign_id=campaign.id, event_type='BUTTON_CLICK').count()
    executions = Event.query.filter_by(campaign_id=campaign.id, event_type='PAYLOAD_EXECUTED').count()
    training_completed = Event.query.filter(
        Event.campaign_id == campaign.id,
        Event.event_type.in_(['TRAINING_COMPLETED', 'TRAINING_ACKNOWLEDGED'])
    ).count()
    
    stats = {
        'total_views': views,
        'total_clicks': clicks,
        'total_executions': executions,
        'total_training_completed': training_completed
    }
    
    events = Event.query.filter_by(campaign_id=campaign.id).order_by(Event.timestamp.desc()).all()
    
    return render_template('admin/campaign_dashboard.html', campaign=campaign, stats=stats, events=events)

@admin_bp.route('/export_csv')
@requires_auth
def export_csv():
    client_filter = request.args.get('client')
    campaign_id = request.args.get('campaign_id')
    
    event_query = Event.query
    
    if campaign_id:
        event_query = event_query.filter_by(campaign_id=campaign_id)
    elif client_filter:
        campaign_ids = [c.id for c in Campaign.query.filter_by(client_name=client_filter).all()]
        event_query = event_query.filter(Event.campaign_id.in_(campaign_ids))
    
    events = event_query.order_by(Event.timestamp.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Timestamp (UTC)', 'Event Type', 'User ID', 'Campaign', 'Client', 'Platform', 'IP Address', 'Hostname', 'Username', 'User Agent'])
    
    for event in events:
        campaign_name = event.campaign.name if event.campaign else 'Unknown'
        client_name = event.campaign.client_name if event.campaign else 'Unknown'
        
        writer.writerow([
            event.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            event.event_type,
            event.user_id,
            campaign_name,
            client_name,
            event.platform,
            event.source_ip,
            event.hostname or '',
            event.username or '',
            event.user_agent
        ])
    
    # Create response
    output.seek(0)
    
    if campaign_id:
        campaign = Campaign.query.get(campaign_id)
        filename_prefix = f"clickfix_campaign_{sanitize_filename(campaign.name)}" if campaign else "clickfix_campaign_unknown"
    elif client_filter:
        filename_prefix = f"clickfix_client_{sanitize_filename(client_filter)}"
    else:
        filename_prefix = "clickfix_events_all"
        
    filename = f"{filename_prefix}_{datetime.datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

@admin_bp.route('/campaign/create', methods=['POST'])
@requires_auth
def create_campaign():
    name = request.form.get('name')
    client = request.form.get('client')
    scenario = request.form.get('scenario')
    trap_slug = request.form.get('trap_slug')
    slug = request.form.get('slug')

    if not name or not scenario:
        return abort(400, "Missing required fields")
    
    # Basic slug validation
    if slug:
        slug = sanitize_filename(slug)
        if Campaign.query.filter_by(slug=slug).first():
            return "Error: Slug already exists", 400
    
    new_campaign = Campaign(name=name, client_name=client, scenario=scenario, trap_slug=trap_slug, slug=slug)
    db.session.add(new_campaign)
    db.session.commit()
    
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/campaign/<int:campaign_id>/delete', methods=['POST'])
@requires_auth
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    Event.query.filter_by(campaign_id=campaign.id).delete()
    Target.query.filter_by(campaign_id=campaign.id).delete()
    
    db.session.delete(campaign)
    db.session.commit()
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/campaign/<int:campaign_id>/edit', methods=['GET', 'POST'])
@requires_auth
def edit_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if request.method == 'POST':
        campaign.name = request.form.get('name')
        campaign.client_name = request.form.get('client')
        campaign.scenario = request.form.get('scenario')
        campaign.trap_slug = request.form.get('trap_slug')
        
        new_slug = request.form.get('slug')
        if new_slug:
            new_slug = sanitize_filename(new_slug)
            # Check if slug exists and belongs to another campaign
            existing = Campaign.query.filter_by(slug=new_slug).first()
            if existing and existing.id != campaign.id:
                return "Error: Slug already exists", 400
            campaign.slug = new_slug
        else:
            campaign.slug = None
            
        db.session.commit()
        return redirect(url_for('admin.campaign_dashboard', campaign_id=campaign.id))
    
    scenarios, traps = get_scenarios_and_traps()
    
    # Get all unique client names for the filter dropdown
    clients = db.session.query(Campaign.client_name).distinct().all()
    client_names = [c[0] for c in clients if c[0]]
    
    return render_template('admin/campaign_edit.html', campaign=campaign, scenarios=scenarios, traps=traps, clients=client_names)


@admin_bp.route('/api/timeline')
@requires_auth
def api_timeline():
    """
    API endpoint for timeline data aggregation (Elasticsearch-style histogram).
    Returns event counts grouped by time intervals.
    
    Query Parameters:
    - start_date: ISO format date string (default: 30 days ago)
    - end_date: ISO format date string (default: now)
    - interval: 'hour', 'day', 'week' (default: 'day')
    - event_type: filter by event type (optional, comma-separated for multiple)
    - campaign_id: filter by campaign ID (optional)
    - client: filter by client name (optional)
    """
    # Parse date range
    end_date = request.args.get('end_date')
    start_date = request.args.get('start_date')
    
    if end_date:
        try:
            end_dt = datetime.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            end_dt = datetime.datetime.utcnow()
    else:
        end_dt = datetime.datetime.utcnow()
    
    if start_date:
        try:
            start_dt = datetime.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            start_dt = end_dt - datetime.timedelta(days=30)
    else:
        start_dt = end_dt - datetime.timedelta(days=30)
    
    interval = request.args.get('interval', 'day')
    event_types = request.args.get('event_type', '').split(',') if request.args.get('event_type') else None
    campaign_id = request.args.get('campaign_id', type=int)
    client_filter = request.args.get('client')
    
    # Build base query with date filter
    query = Event.query.filter(
        Event.timestamp >= start_dt,
        Event.timestamp <= end_dt
    )
    
    # Apply filters
    if event_types and event_types[0]:
        query = query.filter(Event.event_type.in_(event_types))
    
    if campaign_id:
        query = query.filter(Event.campaign_id == campaign_id)
    elif client_filter:
        campaign_ids = [c.id for c in Campaign.query.filter_by(client_name=client_filter).all()]
        query = query.filter(Event.campaign_id.in_(campaign_ids))
    
    # Get all events in range
    events = query.all()
    
    # Group events by interval
    buckets = {}
    
    for event in events:
        if interval == 'hour':
            bucket_key = event.timestamp.replace(minute=0, second=0, microsecond=0)
        elif interval == 'week':
            # Start of week (Monday)
            bucket_key = event.timestamp - datetime.timedelta(days=event.timestamp.weekday())
            bucket_key = bucket_key.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # day (default)
            bucket_key = event.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        
        bucket_str = bucket_key.isoformat()
        
        if bucket_str not in buckets:
            buckets[bucket_str] = {
                'timestamp': bucket_str,
                'total': 0,
                'PAGE_VIEW': 0,
                'BUTTON_CLICK': 0,
                'PAYLOAD_EXECUTED': 0,
                'TRAINING_VIEWED': 0,
                'TRAINING_COMPLETED': 0,
                'TRAINING_ACKNOWLEDGED': 0
            }
        
        buckets[bucket_str]['total'] += 1
        if event.event_type in buckets[bucket_str]:
            buckets[bucket_str][event.event_type] += 1
    
    # Fill in empty buckets for continuous timeline
    current = start_dt
    if interval == 'hour':
        current = current.replace(minute=0, second=0, microsecond=0)
        delta = datetime.timedelta(hours=1)
    elif interval == 'week':
        current = current - datetime.timedelta(days=current.weekday())
        current = current.replace(hour=0, minute=0, second=0, microsecond=0)
        delta = datetime.timedelta(weeks=1)
    else:
        current = current.replace(hour=0, minute=0, second=0, microsecond=0)
        delta = datetime.timedelta(days=1)
    
    while current <= end_dt:
        bucket_str = current.isoformat()
        if bucket_str not in buckets:
            buckets[bucket_str] = {
                'timestamp': bucket_str,
                'total': 0,
                'PAGE_VIEW': 0,
                'BUTTON_CLICK': 0,
                'PAYLOAD_EXECUTED': 0,
                'TRAINING_VIEWED': 0,
                'TRAINING_COMPLETED': 0,
                'TRAINING_ACKNOWLEDGED': 0
            }
        current += delta
    
    # Sort by timestamp and return
    sorted_buckets = sorted(buckets.values(), key=lambda x: x['timestamp'])
    
    return jsonify({
        'start_date': start_dt.isoformat(),
        'end_date': end_dt.isoformat(),
        'interval': interval,
        'buckets': sorted_buckets,
        'total_events': sum(b['total'] for b in sorted_buckets)
    })


@admin_bp.route('/api/events')
@requires_auth
def api_events():
    """
    API endpoint for filtered events list.
    Returns paginated events with filtering support.
    
    Query Parameters:
    - start_date: ISO format date string
    - end_date: ISO format date string
    - event_type: filter by event type (comma-separated for multiple)
    - campaign_id: filter by campaign ID
    - client: filter by client name
    - page: page number (default: 1)
    - per_page: items per page (default: 50, max: 200)
    """
    # Parse date range
    end_date = request.args.get('end_date')
    start_date = request.args.get('start_date')
    
    query = Event.query
    
    if start_date:
        try:
            start_dt = datetime.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Event.timestamp >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Event.timestamp <= end_dt)
        except ValueError:
            pass
    
    # Apply filters
    event_types = request.args.get('event_type', '').split(',') if request.args.get('event_type') else None
    if event_types and event_types[0]:
        query = query.filter(Event.event_type.in_(event_types))
    
    campaign_id = request.args.get('campaign_id', type=int)
    client_filter = request.args.get('client')
    
    if campaign_id:
        query = query.filter(Event.campaign_id == campaign_id)
    elif client_filter:
        campaign_ids = [c.id for c in Campaign.query.filter_by(client_name=client_filter).all()]
        query = query.filter(Event.campaign_id.in_(campaign_ids))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 200)
    
    # Get total count
    total = query.count()
    
    # Get paginated events
    events = query.order_by(Event.timestamp.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    # Serialize events
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'timestamp': event.timestamp.isoformat(),
            'event_type': event.event_type,
            'user_id': event.user_id,
            'campaign_id': event.campaign_id,
            'campaign_name': event.campaign.name if event.campaign else 'Unknown',
            'client_name': event.campaign.client_name if event.campaign else 'Unknown',
            'platform': event.platform,
            'source_ip': event.source_ip,
            'hostname': event.hostname,
            'username': event.username
        })
    
    return jsonify({
        'events': events_data,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })


@admin_bp.route('/api/stats')
@requires_auth
def api_stats():
    """
    API endpoint for dashboard statistics with filtering.
    
    Query Parameters:
    - start_date: ISO format date string
    - end_date: ISO format date string
    - campaign_id: filter by campaign ID
    - client: filter by client name
    """
    query = Event.query
    
    # Parse date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        try:
            start_dt = datetime.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Event.timestamp >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Event.timestamp <= end_dt)
        except ValueError:
            pass
    
    # Apply filters
    campaign_id = request.args.get('campaign_id', type=int)
    client_filter = request.args.get('client')
    
    if campaign_id:
        query = query.filter(Event.campaign_id == campaign_id)
    elif client_filter:
        campaign_ids = [c.id for c in Campaign.query.filter_by(client_name=client_filter).all()]
        query = query.filter(Event.campaign_id.in_(campaign_ids))
    
    # Calculate stats
    stats = {
        'total_views': query.filter(Event.event_type == 'PAGE_VIEW').count(),
        'total_clicks': query.filter(Event.event_type == 'BUTTON_CLICK').count(),
        'total_executions': query.filter(Event.event_type == 'PAYLOAD_EXECUTED').count(),
        'total_training_completed': query.filter(
            Event.event_type.in_(['TRAINING_COMPLETED', 'TRAINING_ACKNOWLEDGED'])
        ).count()
    }
    
    return jsonify(stats)