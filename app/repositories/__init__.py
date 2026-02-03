"""Repositories package."""
from app.repositories.domain_repository import domain_repository, DomainRepository
from app.repositories.config_repository import config_repository, ConfigRepository

__all__ = ['domain_repository', 'config_repository', 'DomainRepository', 'ConfigRepository']
