"""Config API endpoints."""
from flask import request
from flask_restx import Namespace, Resource, fields
from app.services import config_service
from app.api.auth import require_api_auth

ns = Namespace('configs', description='配置管理')

# Models for Swagger documentation
config_model = ns.model('Config', {
    'id': fields.Integer(readonly=True, description='配置ID'),
    'domain_id': fields.Integer(readonly=True, description='域名ID'),
    'language': fields.String(description='语言代码', example='zh-CN'),
    'data': fields.Raw(description='配置数据 (JSON)'),
    'created_at': fields.String(readonly=True, description='创建时间'),
    'updated_at': fields.String(readonly=True, description='更新时间')
})

config_input = ns.model('ConfigInput', {
    'language': fields.String(required=True, description='语言代码', example='zh-CN'),
    'data': fields.Raw(required=True, description='配置数据 (JSON)')
})

config_update = ns.model('ConfigUpdate', {
    'data': fields.Raw(required=True, description='配置数据 (JSON)')
})


@ns.route('/<int:domain_id>/configs')
@ns.param('domain_id', '域名ID')
class ConfigList(Resource):
    """Config list operations for a domain."""

    @ns.doc('list_configs')
    @ns.marshal_list_with(config_model)
    @require_api_auth
    def get(self, domain_id):
        """获取域名的所有配置"""
        configs = config_service.list_configs_by_domain(domain_id)
        return [c.to_dict() for c in configs]

    @ns.doc('create_config')
    @ns.expect(config_input)
    @ns.marshal_with(config_model, code=201)
    @require_api_auth
    def post(self, domain_id):
        """为域名创建配置"""
        data = request.json
        config = config_service.create_config(
            domain_id=domain_id,
            language=data.get('language', 'zh-CN'),
            data=data.get('data', {})
        )
        return config.to_dict(), 201


@ns.route('/<int:domain_id>/configs/<string:language>')
@ns.param('domain_id', '域名ID')
@ns.param('language', '语言代码')
class ConfigResource(Resource):
    """Single config operations."""

    @ns.doc('get_config')
    @ns.marshal_with(config_model)
    @require_api_auth
    def get(self, domain_id, language):
        """获取指定语言的配置"""
        config = config_service.get_config(domain_id, language)
        return config.to_dict()

    @ns.doc('update_config')
    @ns.expect(config_update)
    @ns.marshal_with(config_model)
    @require_api_auth
    def put(self, domain_id, language):
        """更新配置"""
        data = request.json
        config = config_service.update_config(
            domain_id=domain_id,
            language=language,
            data=data.get('data', {})
        )
        return config.to_dict()

    @ns.doc('delete_config')
    @ns.response(204, '删除成功')
    @require_api_auth
    def delete(self, domain_id, language):
        """删除配置"""
        config_service.delete_config(domain_id, language)
        return '', 204
