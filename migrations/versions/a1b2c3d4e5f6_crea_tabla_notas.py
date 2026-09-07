"""crea tabla notas

Revision ID: a1b2c3d4e5f6
Revises: 69ce0446c89a
Create Date: 2026-09-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '69ce0446c89a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'notas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('titulo', sa.String(length=200), nullable=True),
        sa.Column('contenido', sa.Text(), nullable=False),
        sa.Column('tipo_entidad', sa.String(length=30), nullable=False, server_default='general'),
        sa.Column('entidad_id', sa.Integer(), nullable=True),
        sa.Column('prioridad', sa.String(length=10), nullable=False, server_default='media'),
        sa.Column('usuario_creador_id', sa.Integer(), nullable=False),
        sa.Column('usuario_asignado_id', sa.Integer(), nullable=True),
        sa.Column('leida', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('fecha_lectura', sa.DateTime(), nullable=True),
        sa.Column('completada', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('fecha_completada', sa.DateTime(), nullable=True),
        sa.Column('fecha_recordatorio', sa.DateTime(), nullable=True),
        sa.Column('estado_id', sa.Integer(), nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False),
        sa.Column('fecha_actualizacion', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['usuario_creador_id'], ['usuarios.id'], name='fk_notas_usuario_creador_id'),
        sa.ForeignKeyConstraint(['usuario_asignado_id'], ['usuarios.id'], name='fk_notas_usuario_asignado_id'),
        sa.ForeignKeyConstraint(['estado_id'], ['status.id'], name='fk_notas_estado_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('notas', schema=None) as batch_op:
        batch_op.create_index('ix_notas_tipo_entidad_entidad_id', ['tipo_entidad', 'entidad_id'], unique=False)
        batch_op.create_index('ix_notas_usuario_asignado_id', ['usuario_asignado_id'], unique=False)
        batch_op.create_index('ix_notas_fecha_recordatorio', ['fecha_recordatorio'], unique=False)


def downgrade():
    with op.batch_alter_table('notas', schema=None) as batch_op:
        batch_op.drop_index('ix_notas_fecha_recordatorio')
        batch_op.drop_index('ix_notas_usuario_asignado_id')
        batch_op.drop_index('ix_notas_tipo_entidad_entidad_id')
    op.drop_table('notas')
