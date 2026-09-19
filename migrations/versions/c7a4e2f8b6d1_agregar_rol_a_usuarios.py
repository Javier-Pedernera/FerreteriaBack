"""agregar rol a usuarios

Revision ID: c7a4e2f8b6d1
Revises: b3c1f9a7d2e4
Create Date: 2026-09-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7a4e2f8b6d1'
down_revision = 'b3c1f9a7d2e4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rol', sa.String(length=20), nullable=False, server_default='empleado'))


def downgrade():
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.drop_column('rol')
