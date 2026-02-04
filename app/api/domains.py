"""Domain API endpoints."""
from flask import request
from flask_restx import Namespace, Resource, fields
from app.services import domain_service
from app.api.auth import require_api_auth

ns = Namespace('domains', description='域名管理')

# Models for Swagger documentation
domain_model = ns.model('Domain', {
    'id': fields.Integer(readonly=True, description='域名ID'),
    'name': fields.String(required=True, description='域名', example='example.com'),
    'description': fields.String(description='描述'),
    'is_active': fields.Boolean(description='是否启用', default=True),
    'created_at': fields.String(readonly=True, description='创建时间'),
    'updated_at': fields.String(readonly=True, description='更新时间')
})

domain_input = ns.model('DomainInput', {
    'name': fields.String(required=True, description='域名', example='example.com'),
    'description': fields.String(description='描述'),
    'is_active': fields.Boolean(description='是否启用', default=True)
})

domain_update = ns.model('DomainUpdate', {
    'name': fields.String(description='域名'),
    'description': fields.String(description='描述'),
    'is_active': fields.Boolean(description='是否启用')
})


@ns.route('')
class DomainList(Resource):
    """Domain list operations."""

    @ns.doc('list_domains')
    @ns.marshal_list_with(domain_model)
    @ns.param('active_only', '只显示启用的域名', type='boolean', default=False)
    @require_api_auth
    def get(self):
        """获取所有域名"""
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        domains = domain_service.list_domains(active_only)
        return [d.to_dict() for d in domains]

    @ns.doc('create_domain')
    @ns.expect(domain_input)
    @ns.marshal_with(domain_model, code=201)
    @require_api_auth
    def post(self):
        """创建域名"""
        data = request.json
        domain = domain_service.create_domain(
            name=data.get('name'),
            description=data.get('description'),
            is_active=data.get('is_active', True)
        )
        return domain.to_dict(), 201


@ns.route('/<int:id>')
@ns.param('id', '域名ID')
class DomainResource(Resource):
    """Single domain operations."""

    @ns.doc('get_domain')
    @ns.marshal_with(domain_model)
    @require_api_auth
    def get(self, id):
        """获取指定域名"""
        domain = domain_service.get_domain(id)
        return domain.to_dict()

    @ns.doc('update_domain')
    @ns.expect(domain_update)
    @ns.marshal_with(domain_model)
    @require_api_auth
    def put(self, id):
        """更新域名"""
        data = request.json
        domain = domain_service.update_domain(
            domain_id=id,
            name=data.get('name'),
            description=data.get('description'),
            is_active=data.get('is_active')
        )
        return domain.to_dict()

    @ns.doc('delete_domain')
    @ns.response(204, '删除成功')
    @require_api_auth
    def delete(self, id):
        """删除域名"""
        domain_service.delete_domain(id)
        return '', 204
