from app import db
from app.models.persona_autorizada import PersonaAutorizada
from app.models.status import Status

class PersonaAutorizadaService:
    @staticmethod
    def get_default_active_status_id():
        activo = Status.query.filter_by(code='active').first()
        if not activo:
            raise Exception("Estado 'active' no encontrado")
        return activo.id

    @staticmethod
    def get_all():
        return PersonaAutorizada.query.all()

    @staticmethod
    def get_by_id(persona_id):
        return PersonaAutorizada.query.get(persona_id)

    @staticmethod
    def create(data):
        estado_id = PersonaAutorizadaService.get_default_active_status_id()
        print(data)
        persona = PersonaAutorizada(
            cliente_id=data['cliente_id'],
            nombre=data['nombre'],
            apellido=data['apellido'],
            dni=data.get('dni'),
            email=data.get('email'),
            telefono=data.get('telefono'),
            estado_id=estado_id 
        )
        db.session.add(persona)
        db.session.commit()
        db.session.refresh(persona)
        return persona

    @staticmethod
    def update(persona_id, data):
        persona = PersonaAutorizada.query.get(persona_id)
        if not persona:
            return None

        for key, value in data.items():
            if hasattr(persona, key):
                setattr(persona, key, value)
        db.session.commit()
        return persona

    @staticmethod
    def inactivate(persona_id):
        persona = PersonaAutorizada.query.get(persona_id)
        if not persona:
            return None
        estado_suspended = Status.query.filter_by(code='suspended').first()
        if not estado_suspended:
            raise Exception("Estado 'suspended' no encontrado")
        persona.estado_id = estado_suspended.id
        db.session.commit()
        return persona

    @staticmethod
    def delete(persona_id):
        persona = PersonaAutorizada.query.get(persona_id)
        if not persona:
            return None
        db.session.delete(persona)
        db.session.commit()
        return True
