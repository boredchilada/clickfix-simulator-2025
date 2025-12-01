import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models import Campaign, Target

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create database tables."""
    db.create_all()
    print("Initialized the database.")

@click.command("create-test-data")
@with_appcontext
def create_test_data_command():
    """Create a test campaign and user."""
    c = Campaign(name="Test Campaign", client_name="Internal", scenario="teams_error", slug="test-lure")
    db.session.add(c)
    db.session.commit()
    
    t = Target(campaign_id=c.id, user_id="demo_victim", email="demo@example.com", department="IT")
    db.session.add(t)
    db.session.commit()
    print("Created test campaign and user 'demo_victim'")

def register_commands(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_test_data_command)