"""Agregar nombre_columna_codigo_barras a PlantillaImportacion

Revision ID: c4d7e9f1a2b6
Revises: b6d1f2a9c7e3
Create Date: 2026-11-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4d7e9f1a2b6'
down_revision = 'b6d1f2a9c7e3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('plantillas_importacion', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nombre_columna_codigo_barras', sa.String(length=100), nullable=True))


def downgrade():
    with op.batch_alter_table('plantillas_importacion', schema=None) as batch_op:
        batch_op.drop_column('nombre_columna_codigo_barras')
