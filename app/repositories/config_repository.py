"""Config repository for database operations."""
from typing import Optional, List
from app.extensions import db
from app.models.config import Config


class ConfigRepository:
    """Repository for Config CRUD operations."""

    def create(self, domain_id: int, language: str, data: dict) -> Config:
        """Create a new config."""
        config = Config(domain_id=domain_id, language=language, data=data or {})
        db.session.add(config)
        db.session.commit()
        return config

    def get_by_id(self, config_id: int) -> Optional[Config]:
        """Get config by ID."""
        return db.session.get(Config, config_id)

    def get_by_domain_and_language(self, domain_id: int, language: str) -> Optional[Config]:
        """Get config by domain ID and language."""
        return Config.query.filter_by(domain_id=domain_id, language=language).first()

    def get_all_by_domain(self, domain_id: int) -> List[Config]:
        """Get all configs for a domain."""
        return Config.query.filter_by(domain_id=domain_id).order_by(Config.language).all()

    def update(self, config_id: int, data: dict) -> Optional[Config]:
        """Update config data."""
        config = self.get_by_id(config_id)
        if not config:
            return None

        config.data = data
        db.session.commit()
        return config

    def update_by_domain_and_language(self, domain_id: int, language: str,
                                      data: dict) -> Optional[Config]:
        """Update config by domain and language."""
        config = self.get_by_domain_and_language(domain_id, language)
        if not config:
            return None

        config.data = data
        db.session.commit()
        return config

    def delete(self, config_id: int) -> bool:
        """Delete config by ID."""
        config = self.get_by_id(config_id)
        if not config:
            return False

        db.session.delete(config)
        db.session.commit()
        return True

    def delete_by_domain_and_language(self, domain_id: int, language: str) -> bool:
        """Delete config by domain and language."""
        config = self.get_by_domain_and_language(domain_id, language)
        if not config:
            return False

        db.session.delete(config)
        db.session.commit()
        return True


# Singleton instance
config_repository = ConfigRepository()
