"""Query API endpoint for config lookup with language fallback."""
from flask import request
from flask_restx import Namespace, Resource, fields
from app.services import config_service

ns = Namespace('query', description='配置查询')

# Models for Swagger documentation
language_query_result = ns.model('LanguageQueryResult', {
    'domain': fields.String(description='请求的域名'),
    'actual_domain': fields.String(description='实际返回配置的域名'),
    'language': fields.String(description='实际返回的语言'),
    'requested_language': fields.String(description='请求的语言'),
    'is_fallback': fields.Boolean(description='是否回退到默认语言'),
    'is_domain_fallback': fields.Boolean(description='是否回退到其他域名'),
    'data': fields.Raw(description='配置数据')
})

default_query_result = ns.model('DefaultQueryResult', {
    'domain': fields.String(description='请求的域名'),
    'actual_domain': fields.String(description='实际返回配置的域名'),
    'language': fields.String(description='固定为 default'),
    'requested_language': fields.String(description='固定为 null'),
    'is_fallback': fields.Boolean(description='固定为 false'),
    'is_domain_fallback': fields.Boolean(description='是否回退到其他域名'),
    'data': fields.Raw(description='默认配置数据')
})


@ns.route('/language')
class QueryLanguageResource(Resource):
    """Query language config by domain with fallback."""

    @ns.doc('query_language_config')
    @ns.param('domain', '域名', required=True, example='example.com')
    @ns.param('lang', '语言代码', required=False, example='en')
    @ns.marshal_with(language_query_result)
    def get(self):
        """
        查询语言配置

        支持语言回退：如果请求的语言配置不存在，会自动回退到默认语言 (zh-CN)。
        响应中的 is_fallback 字段表示是否发生了回退。
        """
        domain = request.args.get('domain')
        language = request.args.get('lang')

        if not domain:
            from app.services import ValidationError
            raise ValidationError("缺少必需参数: domain")

        result = config_service.get_language_config_with_fallback(domain, language)
        return result


@ns.route('/default')
class QueryDefaultResource(Resource):
    """Query domain default config (language agnostic)."""

    @ns.doc('query_default_config')
    @ns.param('domain', '域名', required=True, example='example.com')
    @ns.marshal_with(default_query_result)
    def get(self):
        """查询域名默认配置（语言无关）"""
        domain = request.args.get('domain')

        if not domain:
            from app.services import ValidationError
            raise ValidationError("缺少必需参数: domain")

        result = config_service.get_default_config_with_fallback(domain)
        return result
