from flask import Flask
from flask_babel import Babel
from flask_cors import CORS

from config import SECRET_KEY
from database import add_default_listings, init_db
from routes import register_blueprints
from routes.payments import payments_bp
from seed import seed_demo_data
from utils.translations import inject_translation_helpers, select_locale


def _alias_endpoint(app, old_endpoint, new_endpoint):
    if old_endpoint in {r.endpoint for r in app.url_map.iter_rules()}:
        return
    for rule in list(app.url_map.iter_rules()):
        if rule.endpoint == new_endpoint:
            methods = sorted(m for m in rule.methods if m not in {'HEAD', 'OPTIONS'})
            app.add_url_rule(rule.rule, endpoint=old_endpoint, view_func=app.view_functions[new_endpoint], methods=methods)


def _register_legacy_endpoint_aliases(app):
    aliases = {
        'index': 'auth.index', 'about': 'auth.about', 'market': 'auth.market', 'signup': 'auth.signup',
        'signin': 'auth.signin', 'signout': 'auth.signout', 'set_language': 'auth.set_language',
        'rentdashboard': 'dashboard.rentdashboard', 'listdashboard': 'dashboard.listdashboard',
        'renting': 'dashboard.renting', 'heatmap': 'dashboard.heatmap',
        'mechanics_list': 'mechanics.mechanics_list', 'mechanic_register': 'mechanics.mechanic_register',
        'mechanic_dashboard': 'mechanics.mechanic_dashboard',
        'update_mechanic_availability': 'mechanics.update_mechanic_availability',
        'update_mechanic_request_status': 'mechanics.update_mechanic_request_status',
        'listing': 'listings.listing', 'create_listing': 'listings.create_listing', 'assets': 'listings.assets',
    }
    for old, new in aliases.items():
        _alias_endpoint(app, old, new)


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    CORS(app)

    Babel(app, locale_selector=select_locale)
    app.context_processor(inject_translation_helpers)

    register_blueprints(app)
    app.register_blueprint(payments_bp)
    _register_legacy_endpoint_aliases(app)

    with app.app_context():
        init_db()
        seed_demo_data()
        add_default_listings()

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
