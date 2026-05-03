from .auth import bp as auth_bp
from .listings import bp as listings_bp
from .rentals import bp as rentals_bp
from .dashboard import bp as dashboard_bp
from .mechanics import bp as mechanics_bp
from .notifications import bp as notifications_bp
from .whatsapp import whatsapp_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(rentals_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(mechanics_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(whatsapp_bp)
