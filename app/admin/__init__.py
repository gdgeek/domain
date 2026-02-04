"""Admin package."""
from flask import Blueprint
import os

template_folder = os.path.join(os.path.dirname(__file__), 'templates')
admin_bp = Blueprint('admin', __name__, template_folder=template_folder)

# Import routes after blueprint is created
from app.admin import routes  # noqa: F401, E402
