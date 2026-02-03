"""Domain service for business logic."""
from typing import Optional, List
from app.models.domain import Domain


class ValidationError(Exception):
    """Validation error exception."""
    pass


class NotFoundError(Exception):
    """Resource not found exception."""
    pass


class DuplicateError(Exception):
    """Duplicate entry exception."""
    pass


class DomainService:
    """Service for domain business logic."""
    
    def __init__(self):
        self._domain_repository = None
        self._cache_service = None
    
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
    
    def _validate_name(self, name: str) -> str:
        """Validate domain name."""
        if not name or not name.strip():
            raise ValidationError("域名不能为空")
        name = name.strip().lower()
        if len(name) > 255:
            raise ValidationError("域名长度不能超过255个字符")
        return name
    
    def create_domain(self, name: str, description: str = None, 
                      is_active: bool = True) -> Domain:
        """Create a new domain."""
        name = self._validate_name(name)
        existing = self.domain_repository.get_by_name(name)
        if existing:
            raise DuplicateError(f"域名 '{name}' 已存在")
        return self.domain_repository.create(name, description, is_active)
    
    def get_domain(self, domain_id: int) -> Domain:
        """Get domain by ID."""
        domain = self.domain_repository.get_by_id(domain_id)
        if not domain:
            raise NotFoundError(f"域名 ID {domain_id} 不存在")
        return domain
    
    def get_domain_by_name(self, name: str) -> Domain:
        """Get domain by name."""
        domain = self.domain_repository.get_by_name(name)
        if not domain:
            raise NotFoundError(f"域名 '{name}' 不存在")
        return domain
    
    def list_domains(self, active_only: bool = False) -> List[Domain]:
        """List all domains."""
        return self.domain_repository.get_all(active_only)
    
    def update_domain(self, domain_id: int, name: str = None,
                      description: str = None, is_active: bool = None) -> Domain:
        """Update domain."""
        domain = self.get_domain(domain_id)
        old_name = domain.name
        if name is not None:
            name = self._validate_name(name)
            if name != old_name:
                existing = self.domain_repository.get_by_name(name)
                if existing:
                    raise DuplicateError(f"域名 '{name}' 已存在")
        updated = self.domain_repository.update(domain_id, name, description, is_active)
        if name and name != old_name:
            self.cache_service.invalidate(old_name)
        return updated
    
    def delete_domain(self, domain_id: int) -> bool:
        """Delete domain (cascades to configs)."""
        domain = self.get_domain(domain_id)
        domain_name = domain.name
        result = self.domain_repository.delete(domain_id)
        if result:
            self.cache_service.invalidate(domain_name)
        return result


domain_service = DomainService()
