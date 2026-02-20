"""Config service for business logic."""
from typing import List, Dict, Any
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
        self.cache_service.invalidate(domain.name)
        return config

    def get_config(self, domain_id: int, language: str) -> Config:
        """Get config by domain and language."""
        language = self._validate_language(language)
        config = self.config_repository.get_by_domain_and_language(domain_id, language)
        if not config:
            raise NotFoundError(f"域名 ID {domain_id} 的 {language} 配置不存在")
        return config

    def _resolve_config_with_fallback(self, domain_name: str, language: str = None) -> Dict[str, Any]:
        """Resolve language config and default config with fallback metadata."""
        default_lang = current_app.config.get('DEFAULT_LANGUAGE', 'zh-CN')
        language = language or default_lang

        domain = self.domain_repository.get_by_name(domain_name)
        if not domain:
            raise NotFoundError(f"域名 '{domain_name}' 不存在")
        if not domain.is_active:
            raise NotFoundError(f"域名 '{domain_name}' 已禁用")

        # 尝试获取配置，支持域名回退
        config = None
        actual_domain = domain
        actual_language = language
        is_domain_fallback = False

        # 1. 先查当前域名的请求语言
        config = self.config_repository.get_by_domain_and_language(domain.id, language)

        # 2. 当前域名的默认语言
        if not config and language != default_lang:
            config = self.config_repository.get_by_domain_and_language(domain.id, default_lang)
            actual_language = default_lang

        # 3. 回退域名的请求语言
        if not config and domain.fallback_domain_id:
            fallback = domain.fallback_domain
            if fallback and fallback.is_active:
                config = self.config_repository.get_by_domain_and_language(fallback.id, language)
                if config:
                    actual_domain = fallback
                    actual_language = language
                    is_domain_fallback = True

        # 4. 回退域名的默认语言
        if not config and domain.fallback_domain_id:
            fallback = domain.fallback_domain
            if fallback and fallback.is_active:
                config = self.config_repository.get_by_domain_and_language(fallback.id, default_lang)
                if config:
                    actual_domain = fallback
                    actual_language = default_lang
                    is_domain_fallback = True

        base_domain = actual_domain if config else domain
        default_data = (base_domain.default_config or {}) if base_domain else {}

        if not default_data and not config and domain.fallback_domain_id:
            fallback = domain.fallback_domain
            if fallback and fallback.is_active and fallback.default_config:
                base_domain = fallback
                default_data = fallback.default_config
                is_domain_fallback = True

        return {
            'domain_name': domain_name,
            'requested_language': language,
            'actual_domain': base_domain,
            'actual_language': actual_language,
            'is_domain_fallback': is_domain_fallback,
            'language_config': config,
            'default_data': default_data or {}
        }

    def get_language_config_with_fallback(self, domain_name: str, language: str = None) -> Dict[str, Any]:
        """Get language config only, with language/domain fallback."""
        default_lang = current_app.config.get('DEFAULT_LANGUAGE', 'zh-CN')
        language = language or default_lang
        cache_variant = f"{language}|language"
        cached = self.cache_service.get(domain_name, cache_variant)
        if cached:
            return cached

        resolved = self._resolve_config_with_fallback(domain_name, language)
        config = resolved['language_config']
        if not config:
            raise NotFoundError(f"域名 '{domain_name}' 没有语言配置")

        result = {
            'domain': resolved['domain_name'],
            'actual_domain': resolved['actual_domain'].name,
            'language': resolved['actual_language'],
            'requested_language': resolved['requested_language'],
            'is_fallback': resolved['actual_language'] != resolved['requested_language'],
            'is_domain_fallback': resolved['is_domain_fallback'],
            'data': (config.data if config else {}) or {}
        }
        self.cache_service.set(domain_name, cache_variant, result)
        return result

    def get_default_config_with_fallback(self, domain_name: str) -> Dict[str, Any]:
        """Get domain default config only (language agnostic), with domain fallback."""
        cache_variant = "default"
        cached = self.cache_service.get(domain_name, cache_variant)
        if cached:
            return cached

        resolved = self._resolve_config_with_fallback(domain_name, None)
        default_data = resolved['default_data']
        if not default_data:
            raise NotFoundError(f"域名 '{domain_name}' 没有默认配置")

        result = {
            'domain': resolved['domain_name'],
            'actual_domain': resolved['actual_domain'].name,
            'language': 'default',
            'requested_language': None,
            'is_fallback': False,
            'is_domain_fallback': resolved['is_domain_fallback'],
            'data': default_data
        }
        self.cache_service.set(domain_name, cache_variant, result)
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
        self.cache_service.invalidate(domain.name)
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
        self.cache_service.invalidate(domain.name)
        return result


config_service = ConfigService()
