"""empresa_fiscal_config: datos para la factura (domicilio, iibb, etc.)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('empresa_fiscal_config', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nombre_fantasia', sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column('domicilio', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('ingresos_brutos', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('inicio_actividades', sa.Date(), nullable=True))


def downgrade():
    with op.batch_alter_table('empresa_fiscal_config', schema=None) as batch_op:
        batch_op.drop_column('inicio_actividades')
        batch_op.drop_column('ingresos_brutos')
        batch_op.drop_column('domicilio')
        batch_op.drop_column('nombre_fantasia')
