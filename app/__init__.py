import logging
import os
from flask import Flask
from config import Config
from app.extensions import db
from app.blueprints.main import main_bp
from app.blueprints.admin import admin_bp
from app.blueprints.lure import lure_bp
from app.blueprints.stealth import register_stealth_routes
from app.cli import register_commands

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)

    # --- Logging Setup ---
    logging.basicConfig(filename='app.log', level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s')

    db.init_app(app)

    # Cloud/Proxy Compatibility: Trust X-Forwarded-For headers
    # This ensures request.remote_addr is the actual client IP, not the Load Balancer's IP
    # SECURITY: Only enable when behind a trusted reverse proxy (nginx, AWS ALB, etc.)
    # If exposed directly to the internet, this allows IP spoofing via headers
    if os.environ.get('BEHIND_PROXY', 'false').lower() in ('true', '1', 'yes'):
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
        logging.info("ProxyFix middleware enabled - trusting X-Forwarded-* headers")

    # Enable Write-Ahead Logging (WAL) for better concurrency
    with app.app_context():
        try:
            from sqlalchemy import text
            db.session.execute(text("PRAGMA journal_mode=WAL"))
            db.session.commit()
        except Exception as e:
            logging.warning(f"Could not enable WAL mode: {e}")

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(lure_bp)

    # Register Stealth Routes (Dynamic)
    register_stealth_routes(app)

    register_commands(app)

    return app