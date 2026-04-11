# modules/authentication/__init__.py
from flask import Blueprint

authentication_bp = Blueprint('authentication', __name__)

from . import routes
