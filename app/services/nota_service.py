from datetime import datetime, timezone

from app import db
from app.models.nota import Nota, TIPOS_ENTIDAD_NOTA, PRIORIDADES_NOTA
from app.services.status_service import StatusService


class NotaService:

    @staticmethod
    def _query_activas():
        estado_deleted = StatusService.get_status_by_code('deleted')
        query = Nota.query
        if estado_deleted:
            query = query.filter(Nota.estado_id != estado_deleted.id)
        return query

    @staticmethod
    def get_all_notas(filtros=None):
        """
        Lista notas activas (no eliminadas), con filtros opcionales:
        tipo_entidad, entidad_id, leida, completada, usuario_asignado_id, prioridad
        """
        filtros = filtros or {}
        query = NotaService._query_activas()

        if filtros.get('tipo_entidad'):
            query = query.filter(Nota.tipo_entidad == filtros['tipo_entidad'])
        if filtros.get('entidad_id') is not None:
            query = query.filter(Nota.entidad_id == filtros['entidad_id'])
        if filtros.get('leida') is not None:
            query = query.filter(Nota.leida == filtros['leida'])
        if filtros.get('completada') is not None:
            query = query.filter(Nota.completada == filtros['completada'])
        if filtros.get('usuario_asignado_id') is not None:
            query = query.filter(Nota.usuario_asignado_id == filtros['usuario_asignado_id'])
        if filtros.get('prioridad'):
            query = query.filter(Nota.prioridad == filtros['prioridad'])

        return query.order_by(Nota.fecha_creacion.desc()).all()

    @staticmethod
    def get_nota_by_id(nota_id):
        return Nota.query.get(nota_id)

    @staticmethod
    def get_alertas(usuario_id=None):
        """
        Notas que ameritan mostrarse como alerta: no completadas, y que
        además están sin leer o ya vencieron (fecha_recordatorio <= ahora).
        """
        ahora = datetime.now(timezone.utc)
        query = NotaService._query_activas().filter(Nota.completada.is_(False))

        if usuario_id is not None:
            query = query.filter(Nota.usuario_asignado_id == usuario_id)

        query = query.filter(
            db.or_(
                Nota.leida.is_(False),
                db.and_(Nota.fecha_recordatorio.isnot(None), Nota.fecha_recordatorio <= ahora)
            )
        )

        return query.order_by(Nota.fecha_recordatorio.asc().nullslast(), Nota.fecha_creacion.desc()).all()

    @staticmethod
    def create_nota(data):
        if not data.get('contenido'):
            raise ValueError("El campo 'contenido' es obligatorio")
        if not data.get('usuario_creador_id'):
            raise ValueError("El campo 'usuario_creador_id' es obligatorio")

        tipo_entidad = data.get('tipo_entidad', 'general')
        if tipo_entidad not in TIPOS_ENTIDAD_NOTA:
            raise ValueError(f"tipo_entidad inválido. Valores permitidos: {TIPOS_ENTIDAD_NOTA}")

        prioridad = data.get('prioridad', 'media')
        if prioridad not in PRIORIDADES_NOTA:
            raise ValueError(f"prioridad inválida. Valores permitidos: {PRIORIDADES_NOTA}")

        estado_activo = StatusService.get_status_by_code('active')
        if not estado_activo:
            raise ValueError("No existe el status 'active'")

        nota = Nota(
            titulo=data.get('titulo'),
            contenido=data['contenido'],
            tipo_entidad=tipo_entidad,
            entidad_id=data.get('entidad_id'),
            prioridad=prioridad,
            usuario_creador_id=data['usuario_creador_id'],
            usuario_asignado_id=data.get('usuario_asignado_id'),
            fecha_recordatorio=data.get('fecha_recordatorio'),
            estado_id=estado_activo.id,
        )
        db.session.add(nota)
        db.session.commit()
        return nota

    @staticmethod
    def update_nota(nota_id, data):
        nota = Nota.query.get(nota_id)
        if not nota:
            return None

        if 'tipo_entidad' in data and data['tipo_entidad'] not in TIPOS_ENTIDAD_NOTA:
            raise ValueError(f"tipo_entidad inválido. Valores permitidos: {TIPOS_ENTIDAD_NOTA}")
        if 'prioridad' in data and data['prioridad'] not in PRIORIDADES_NOTA:
            raise ValueError(f"prioridad inválida. Valores permitidos: {PRIORIDADES_NOTA}")

        nota.titulo = data.get('titulo', nota.titulo)
        nota.contenido = data.get('contenido', nota.contenido)
        nota.tipo_entidad = data.get('tipo_entidad', nota.tipo_entidad)
        nota.entidad_id = data.get('entidad_id', nota.entidad_id)
        nota.prioridad = data.get('prioridad', nota.prioridad)
        nota.usuario_asignado_id = data.get('usuario_asignado_id', nota.usuario_asignado_id)
        nota.fecha_recordatorio = data.get('fecha_recordatorio', nota.fecha_recordatorio)

        db.session.commit()
        return nota

    @staticmethod
    def marcar_leida(nota_id, leida=True):
        nota = Nota.query.get(nota_id)
        if not nota:
            return None
        nota.leida = leida
        nota.fecha_lectura = datetime.now(timezone.utc) if leida else None
        db.session.commit()
        return nota

    @staticmethod
    def marcar_completada(nota_id, completada=True):
        nota = Nota.query.get(nota_id)
        if not nota:
            return None
        nota.completada = completada
        nota.fecha_completada = datetime.now(timezone.utc) if completada else None
        db.session.commit()
        return nota

    @staticmethod
    def delete_nota(nota_id):
        """Soft delete: marca la nota con estado 'deleted' en vez de borrarla."""
        nota = Nota.query.get(nota_id)
        if not nota:
            return False

        estado_deleted = StatusService.get_status_by_code('deleted')
        if not estado_deleted:
            raise ValueError("No existe el status 'deleted'")

        nota.estado_id = estado_deleted.id
        db.session.commit()
        return True
