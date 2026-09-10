"""factura: cliente_id nullable + datos de receptor sin cliente

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('facturas', schema=None) as batch_op:
        batch_op.alter_column('cliente_id', existing_type=sa.INTEGER(), nullable=True)
        batch_op.add_column(sa.Column('receptor_nombre', sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column('receptor_doc_tipo', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('receptor_doc_nro', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('receptor_condicion_iva', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('facturas', schema=None) as batch_op:
        batch_op.drop_column('receptor_condicion_iva')
        batch_op.drop_column('receptor_doc_nro')
        batch_op.drop_column('receptor_doc_tipo')
        batch_op.drop_column('receptor_nombre')
        batch_op.alter_column('cliente_id', existing_type=sa.INTEGER(), nullable=False)
