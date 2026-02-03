"""API package."""
from flask import Blueprint
from flask_restx import Api

api_bp = Blueprint('api', __name__)

# Swagger 认证配置
authorizations = {
    'password': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-Admin-Password',
        'description': '管理员密码'
    }
}

api = Api(
    api_bp,
    version='1.0',
    title='Domain Config API',
    description='轻量级域名配置服务 API',
    doc='/docs',
    authorizations=authorizations,
    security='password'
)

# Register error handlers
from app.api.errors import register_error_handlers
register_error_handlers(api)

# Import and register namespaces
from app.api.domains import ns as domains_ns
from app.api.configs import ns as configs_ns
from app.api.query import ns as query_ns

api.add_namespace(domains_ns, path='/domains')
api.add_namespace(configs_ns, path='/domains')
api.add_namespace(query_ns, path='/query')
