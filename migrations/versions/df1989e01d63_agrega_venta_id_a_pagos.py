"""agrega venta_id a pagos
 
Revision ID: df1989e01d63
Revises: 711d5f674ec2
Create Date: 2026-08-23 19:13:25.058083
 
"""
from alembic import op
import sqlalchemy as sa
 
 
# revision identifiers, used by Alembic.
revision = 'df1989e01d63'
down_revision = '711d5f674ec2'
branch_labels = None
depends_on = None
 
 
def upgrade():
    with op.batch_alter_table('pagos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('venta_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_pagos_venta_id', 'ventas', ['venta_id'], ['id'])
 
 
def downgrade():
    with op.batch_alter_table('pagos', schema=None) as batch_op:
        batch_op.drop_constraint('fk_pagos_venta_id', type_='foreignkey')
        batch_op.drop_column('venta_id')