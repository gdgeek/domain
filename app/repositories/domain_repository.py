"""Domain repository for database operations."""
from typing import Optional, List
from app.extensions import db
from app.models.domain import Domain


class DomainRepository:
    """Repository for Domain CRUD operations."""
    
    def create(self, name: str, description: str = None, is_active: bool = True) -> Domain:
        """Create a new domain."""
        domain = Domain(name=name, description=description, is_active=is_active)
        db.session.add(domain)
        db.session.commit()
        return domain
    
    def get_by_id(self, domain_id: int) -> Optional[Domain]:
        """Get domain by ID."""
        return db.session.get(Domain, domain_id)
    
    def get_by_name(self, name: str) -> Optional[Domain]:
        """Get domain by name."""
        return Domain.query.filter_by(name=name).first()
    
    def get_all(self, active_only: bool = False) -> List[Domain]:
        """Get all domains."""
        query = Domain.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(Domain.id.desc()).all()
    
    def update(self, domain_id: int, name: str = None, 
               description: str = None, is_active: bool = None) -> Optional[Domain]:
        """Update domain."""
        domain = self.get_by_id(domain_id)
        if not domain:
            return None
        
        if name is not None:
            domain.name = name
        if description is not None:
            domain.description = description
        if is_active is not None:
            domain.is_active = is_active
        
        db.session.commit()
        return domain
    
    def delete(self, domain_id: int) -> bool:
        """Delete domain (cascades to configs)."""
        domain = self.get_by_id(domain_id)
        if not domain:
            return False
        
        db.session.delete(domain)
        db.session.commit()
        return True


# Singleton instance
domain_repository = DomainRepository()
