"""API authentication."""
from functools import wraps
from flask import request, current_app
from flask_restx import abort


def require_api_auth(f):
    """Decorator to require password authentication for API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_password = current_app.config.get('ADMIN_PASSWORD')
        # No password configured = no auth required
        if not admin_password:
            return f(*args, **kwargs)
        
        # Check Authorization header (Basic auth with password only)
        auth = request.authorization
        if auth and auth.password == admin_password:
            return f(*args, **kwargs)
        
        # Check X-Admin-Password header
        header_password = request.headers.get('X-Admin-Password')
        if header_password == admin_password:
            return f(*args, **kwargs)
        
        abort(401, '需要认证')
    return decorated_function
