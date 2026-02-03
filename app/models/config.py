"""Config model."""
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from app.extensions import db


class Config(db.Model):
    """Config model for storing domain configurations with language support."""
    __tablename__ = 'configs'
    
    id = db.Column(db.Integer, primary_key=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('domains.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    language = db.Column(db.String(10), nullable=False, default='zh-CN', index=True)
    data = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint on (domain_id, language)
    __table_args__ = (
        db.UniqueConstraint('domain_id', 'language', name='uq_config_domain_language'),
        db.Index('idx_configs_domain_language', 'domain_id', 'language'),
    )
    
    def to_dict(self):
        """Convert config to dictionary."""
        return {
            'id': self.id,
            'domain_id': self.domain_id,
            'language': self.language,
            'data': self.data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Config domain_id={self.domain_id} lang={self.language}>'
