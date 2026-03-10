from datetime import datetime, timezone
from app import db


class ArcaToken(db.Model):
    __tablename__ = 'arca_tokens'

    id = db.Column(db.Integer, primary_key=True)

    token = db.Column(db.Text, nullable=False)
    sign = db.Column(db.Text, nullable=False)

    expiration_time = db.Column(db.DateTime, nullable=False)

    fecha_creacion = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    def is_valid(self):
        if not self.expiration_time:
            return False

        now = datetime.now(timezone.utc)

        # Si expiration_time viene sin tz, lo convertimos
        if self.expiration_time.tzinfo is None:
            expiration = self.expiration_time.replace(tzinfo=timezone.utc)
        else:
            expiration = self.expiration_time

        return expiration > now

    def __repr__(self):
        return f'<ArcaToken vence={self.expiration_time}>'