from flask import Blueprint, render_template
from flask_login import login_required, current_user
from ..authentication.decorators import admin_required, plan_required


views_bp = Blueprint('views', __name__)

@views_bp.route('/')
@login_required
@plan_required
def index():
    date_expiry = current_user.date_expiry.strftime('%Y-%m-%d') if current_user.date_expiry else 'Permanente'
    return render_template('home/index.html', date=date_expiry)

@views_bp.route('/user')
@login_required
def user():
    date_expiry = current_user.date_expiry.strftime('%Y-%m-%d') if current_user.date_expiry else 'Permanente'
    return render_template('home/user.html', date=date_expiry, name = current_user.username)

@views_bp.route('/users')
@login_required
@admin_required
def admin_users():
    date_expiry = current_user.date_expiry.strftime('%Y-%m-%d') if current_user.date_expiry else 'Permanente'
    return render_template('home/users.html', date=date_expiry)


