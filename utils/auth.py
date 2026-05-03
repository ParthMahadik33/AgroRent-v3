from functools import wraps
from flask import flash, redirect, session, url_for
from utils.translations import translate_text


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash(translate_text("alerts.login_required"), "warning")
            return redirect(url_for("signin"))
        return f(*args, **kwargs)
    return decorated_function
