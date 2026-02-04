"""Domain model."""
from datetime import datetime
from app.extensions import db


class Domain(db.Model):
    """Domain model for storing website domains."""
    __tablename__ = 'domains'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    fallback_domain_id = db.Column(db.Integer, db.ForeignKey('domains.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to configs
    configs = db.relationship('Config', backref='domain', lazy='dynamic',
                              cascade='all, delete-orphan')

    # Self-referential relationship for fallback
    fallback_domain = db.relationship('Domain', remote_side=[id], backref='aliases')

    def to_dict(self):
        """Convert domain to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'fallback_domain_id': self.fallback_domain_id,
            'fallback_domain_name': self.fallback_domain.name if self.fallback_domain else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Domain {self.name}>'
