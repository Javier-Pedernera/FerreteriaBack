"""Agregar fecha_ultimo_archivo a PlantillaImportacion

Revision ID: d8e2f4a6b9c1
Revises: c4d7e9f1a2b6
Create Date: 2026-11-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8e2f4a6b9c1'
down_revision = 'c4d7e9f1a2b6'
branch_labels = None
depends_on = None


def upgrade():
    # fecha_ultimo_archivo se actualiza al subir un Excel nuevo, a diferencia
    # de fecha_ultima_lista que solo se actualiza si esos datos se llegaron
    # a importar con exito.
    with op.batch_alter_table('plantillas_importacion', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fecha_ultimo_archivo', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('plantillas_importacion', schema=None) as batch_op:
        batch_op.drop_column('fecha_ultimo_archivo')
