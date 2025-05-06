from .. import db

class Status(db.Model):
    __tablename__ = 'status'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    label = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<Status {self.code}>'

    def serialize(self):
        return {
            'id': self.id,
            'code': self.code,
            'label': self.label,
            'description': self.description
        }