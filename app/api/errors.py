"""API error handlers."""
from flask_restx import Api
from app.services import ValidationError, NotFoundError, DuplicateError


def register_error_handlers(api: Api):
    """Register error handlers for the API."""

    @api.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle validation errors - 400."""
        return {'error': {'code': 'VALIDATION_ERROR', 'message': str(error)}}, 400

    @api.errorhandler(NotFoundError)
    def handle_not_found_error(error):
        """Handle not found errors - 404."""
        return {'error': {'code': 'NOT_FOUND', 'message': str(error)}}, 404

    @api.errorhandler(DuplicateError)
    def handle_duplicate_error(error):
        """Handle duplicate entry errors - 409."""
        return {'error': {'code': 'DUPLICATE_ENTRY', 'message': str(error)}}, 409

    @api.errorhandler(Exception)
    def handle_generic_error(error):
        """Handle generic errors - 500."""
        import logging
        logging.exception("Internal server error")
        return {'error': {'code': 'INTERNAL_ERROR', 'message': '服务器内部错误'}}, 500
