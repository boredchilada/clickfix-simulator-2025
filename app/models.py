import datetime
from app.extensions import db

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    client_name = db.Column(db.String(100), nullable=True, default='Default')
    scenario = db.Column(db.String(50), nullable=False)
    trap_slug = db.Column(db.String(50), nullable=True)
    slug = db.Column(db.String(100), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    targets = db.relationship('Target', backref='campaign', lazy=True)
    events = db.relationship('Event', backref='campaign', lazy=True)

class Target(db.Model):
    __tablename__ = 'targets'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    user_id = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120))
    department = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # PAGE_VIEW, BUTTON_CLICK, PAYLOAD_EXECUTED
    source_ip = db.Column(db.String(50))
    hostname = db.Column(db.String(100))
    username = db.Column(db.String(100))
    user_agent = db.Column(db.String(255))
    platform = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)