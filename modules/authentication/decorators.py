from functools import wraps
from flask import redirect, url_for, flash, render_template
from flask_login import current_user
from datetime import datetime

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            #flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('views.index'))
        return f(*args, **kwargs)
    return decorated_function

def plan_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('authentication.login'))
        if current_user.date_expiry is None or current_user.date_expiry > datetime.utcnow().date():
            return f(*args, **kwargs)
        else:
            #flash('Your plan has expired.', 'danger')
            return render_template('home/plan_expired.html', date="Expirado")
    return decorated_function