"""Config service for business logic."""
from typing import Optional, List, Dict, Any
from flask import current_app
from app.services.domain_service import ValidationError, NotFoundError, DuplicateError
from app.models.config import Config


class ConfigService:
    """Service for config business logic."""
    
    def __init__(self):
        self._config_repository = None
        self._domain_repository = None
        self._cache_service = None
    
    @property
    def config_repository(self):
        if self._config_repository is None:
            from app.repositories.config_repository import config_repository
            self._config_repository = config_repository
        return self._config_repository
    
    @property
    def domain_repository(self):
        if self._domain_repository is None:
            from app.repositories.domain_repository import domain_repository
            self._domain_repository = domain_repository
        return self._domain_repository
    
    @property
    def cache_service(self):
        if self._cache_service is None:
            from app.services.cache_service import cache_service
            self._cache_service = cache_service
        return self._cache_service
    
    def _validate_language(self, language: str) -> str:
        """Validate language code."""
        if not language or not language.strip():
            return current_app.config.get('DEFAULT_LANGUAGE', 'zh-CN')
        language = language.strip()
        supported = current_app.config.get('SUPPORTED_LANGUAGES', 
                                           ['zh-CN', 'en', 'ja', 'zh-TW', 'th'])
        if language not in supported:
            raise ValidationError(f"不支持的语言: {language}")
        return language
    
    def create_config(self, domain_id: int, language: str, data: dict) -> Config:
        """Create a new config for domain."""
        domain = self.domain_repository.get_by_id(domain_id)
        if not domain:
            raise NotFoundError(f"域名 ID {domain_id} 不存在")
        language = self._validate_language(language)
        existing = self.config_repository.get_by_domain_and_language(domain_id, language)
        if existing:
            raise DuplicateError(f"域名 ID {domain_id} 的 {language} 配置已存在")
        config = self.config_repository.create(domain_id, language, data or {})
        self.cache_service.invalidate(domain.name, language)
        return config
    
    def get_config(self, domain_id: int, language: str) -> Config:
        """Get config by domain and language."""
        language = self._validate_language(language)
        config = self.config_repository.get_by_domain_and_language(domain_id, language)
        if not config:
            raise NotFoundError(f"域名 ID {domain_id} 的 {language} 配置不存在")
        return config
    
    def get_config_with_fallback(self, domain_name: str, language: str = None) -> Dict[str, Any]:
        """Get config with language fallback."""
        default_lang = current_app.config.get('DEFAULT_LANGUAGE', 'zh-CN')
        language = language or default_lang
        cached = self.cache_service.get(domain_name, language)
        if cached:
            return cached
        domain = self.domain_repository.get_by_name(domain_name)
        if not domain:
            raise NotFoundError(f"域名 '{domain_name}' 不存在")
        if not domain.is_active:
            raise NotFoundError(f"域名 '{domain_name}' 已禁用")
        config = self.config_repository.get_by_domain_and_language(domain.id, language)
        actual_language = language
        if not config and language != default_lang:
            config = self.config_repository.get_by_domain_and_language(domain.id, default_lang)
            actual_language = default_lang
        if not config:
            raise NotFoundError(f"域名 '{domain_name}' 没有配置")
        result = {
            'domain': domain_name,
            'language': actual_language,
            'requested_language': language,
            'is_fallback': actual_language != language,
            'data': config.data
        }
        self.cache_service.set(domain_name, language, result)
        return result
    
    def list_configs_by_domain(self, domain_id: int) -> List[Config]:
        """List all configs for a domain."""
        domain = self.domain_repository.get_by_id(domain_id)
        if not domain:
            raise NotFoundError(f"域名 ID {domain_id} 不存在")
        return self.config_repository.get_all_by_domain(domain_id)
    
    def update_config(self, domain_id: int, language: str, data: dict) -> Config:
        """Update config data."""
        domain = self.domain_repository.get_by_id(domain_id)
        if not domain:
            raise NotFoundError(f"域名 ID {domain_id} 不存在")
        language = self._validate_language(language)
        config = self.config_repository.update_by_domain_and_language(domain_id, language, data)
        if not config:
            raise NotFoundError(f"域名 ID {domain_id} 的 {language} 配置不存在")
        self.cache_service.invalidate(domain.name, language)
        return config
    
    def delete_config(self, domain_id: int, language: str) -> bool:
        """Delete config."""
        domain = self.domain_repository.get_by_id(domain_id)
        if not domain:
            raise NotFoundError(f"域名 ID {domain_id} 不存在")
        language = self._validate_language(language)
        result = self.config_repository.delete_by_domain_and_language(domain_id, language)
        if not result:
            raise NotFoundError(f"域名 ID {domain_id} 的 {language} 配置不存在")
        self.cache_service.invalidate(domain.name, language)
        return result


config_service = ConfigService()
