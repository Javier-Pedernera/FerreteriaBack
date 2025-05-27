from app.models import Status
from app import db

class StatusService:

    @staticmethod
    def get_all_status():
        return Status.query.all()

    @staticmethod
    def get_status_by_id(status_id):
        return Status.query.get(status_id)

    @staticmethod
    def create_status(data):
        nuevo_status = Status(
            code=data['code'],
            label=data['label'],
            description=data.get('description')
        )
        db.session.add(nuevo_status)
        db.session.commit()
        return nuevo_status

    @staticmethod
    def update_status(status_id, data):
        status = Status.query.get(status_id)
        if not status:
            return None
        status.code = data.get('code', status.code)
        status.label = data.get('label', status.label)
        status.description = data.get('description', status.description)
        db.session.commit()
        return status

    @staticmethod
    def delete_status(status_id):
        status = Status.query.get(status_id)
        if not status:
            return None
        db.session.delete(status)
        db.session.commit()
        return status
