"""crea tabla anuncios

Revision ID: b3c1f9a7d2e4
Revises: e5f6a7b8c9d0
Create Date: 2026-09-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3c1f9a7d2e4'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'anuncios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('posicion', sa.String(length=20), nullable=False, server_default='carrusel'),
        sa.Column('tipo', sa.String(length=10), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('titulo', sa.String(length=200), nullable=True),
        sa.Column('duracion_ms', sa.Integer(), nullable=True),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False),
        sa.Column('fecha_actualizacion', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('anuncios', schema=None) as batch_op:
        batch_op.create_index('ix_anuncios_posicion_orden', ['posicion', 'orden'], unique=False)


def downgrade():
    with op.batch_alter_table('anuncios', schema=None) as batch_op:
        batch_op.drop_index('ix_anuncios_posicion_orden')
    op.drop_table('anuncios')
