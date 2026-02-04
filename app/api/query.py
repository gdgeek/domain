"""Query API endpoint for config lookup with language fallback."""
from flask import request
from flask_restx import Namespace, Resource, fields
from app.services import config_service

ns = Namespace('query', description='配置查询')

# Models for Swagger documentation
query_result = ns.model('QueryResult', {
    'domain': fields.String(description='域名'),
    'language': fields.String(description='实际返回的语言'),
    'requested_language': fields.String(description='请求的语言'),
    'is_fallback': fields.Boolean(description='是否回退到默认语言'),
    'data': fields.Raw(description='配置数据')
})


@ns.route('')
class QueryResource(Resource):
    """Query config by domain and language."""

    @ns.doc('query_config')
    @ns.param('domain', '域名', required=True, example='example.com')
    @ns.param('lang', '语言代码', required=False, example='en')
    @ns.marshal_with(query_result)
    def get(self):
        """
        查询域名配置

        支持语言回退：如果请求的语言配置不存在，会自动回退到默认语言 (zh-CN)。
        响应中的 is_fallback 字段表示是否发生了回退。
        """
        domain = request.args.get('domain')
        language = request.args.get('lang')

        if not domain:
            from app.services import ValidationError
            raise ValidationError("缺少必需参数: domain")

        result = config_service.get_config_with_fallback(domain, language)
        return result
