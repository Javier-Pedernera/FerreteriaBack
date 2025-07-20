from app import db
from app.models.cliente import Cliente
from app.models.persona_autorizada import PersonaAutorizada
from app.services.status_service import StatusService

class ClienteService:

    @staticmethod
    def get_all_clientes():
        return Cliente.query.order_by(Cliente.nombre.asc()).all()

    @staticmethod
    def get_cliente_by_id(cliente_id):
        return Cliente.query.get(cliente_id)

    @staticmethod
    def create_cliente(data):
        cliente = Cliente(
            nombre=data['nombre'],
            razon_social=data.get('razon_social'),
            cuit=data.get('cuit'),
            email=data.get('email'),
            telefono=data.get('telefono'),
            direccion=data.get('direccion'),
            estado_id=data['estado_id'],
            cuenta_corriente_activa=data.get('cuenta_corriente_activa', False)
        )
        db.session.add(cliente)
        db.session.commit()
        return cliente

    @staticmethod
    def update_cliente(cliente_id, data):
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return None

        cliente.nombre = data.get('nombre', cliente.nombre)
        cliente.razon_social = data.get('razon_social', cliente.razon_social)
        cliente.cuit = data.get('cuit', cliente.cuit)
        cliente.email = data.get('email', cliente.email)
        cliente.telefono = data.get('telefono', cliente.telefono)
        cliente.direccion = data.get('direccion', cliente.direccion)
        cliente.estado_id = data.get('estado_id', cliente.estado_id)
        cliente.cuenta_corriente_activa = data.get('cuenta_corriente_activa', cliente.cuenta_corriente_activa)

        # Manejo de personas autorizadas (si se envían)
        personas_data = data.get('personas_autorizadas')
        if personas_data is not None:
            # Borrar las anteriores
            PersonaAutorizada.query.filter_by(cliente_id=cliente.id).delete()

            # Crear nuevas personas con estado 'activo'
            estado_activo = StatusService.get_status_by_code('active')
            for persona in personas_data:
                nueva = PersonaAutorizada(
                    cliente_id=cliente.id,
                    nombre=persona['nombre'],
                    apellido=persona['apellido'],
                    dni=persona.get('dni'),
                    email=persona.get('email'),
                    telefono=persona.get('telefono'),
                    estado_id=estado_activo.id if estado_activo else cliente.estado_id,
                )
                db.session.add(nueva)

        db.session.commit()
        return cliente