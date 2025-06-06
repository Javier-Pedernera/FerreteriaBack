"""Agrega campos fecha_llegada y fecha_pago a pedidos_proveedor

Revision ID: 16b1fe6df192
Revises: cf9544dab5f4
Create Date: 2025-05-06 08:47:23.972507

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '16b1fe6df192'
down_revision = 'cf9544dab5f4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pedidos_proveedor', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fecha_llegada', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('fecha_pago', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pedidos_proveedor', schema=None) as batch_op:
        batch_op.drop_column('fecha_pago')
        batch_op.drop_column('fecha_llegada')

    # ### end Alembic commands ###
