"""crea tablas presupuestos y detalles_presupuesto

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'presupuestos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=True),
        sa.Column('cliente_nombre', sa.String(length=150), nullable=True),
        sa.Column('cliente_cuit', sa.String(length=20), nullable=True),
        sa.Column('cliente_telefono', sa.String(length=50), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('total', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('estado', sa.String(length=20), nullable=False, server_default='pendiente'),
        sa.Column('venta_id', sa.Integer(), nullable=True),
        sa.Column('usuario_creador_id', sa.Integer(), nullable=False),
        sa.Column('eliminado', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False),
        sa.Column('fecha_actualizacion', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], name='fk_presupuestos_cliente_id'),
        sa.ForeignKeyConstraint(['venta_id'], ['ventas.id'], name='fk_presupuestos_venta_id'),
        sa.ForeignKeyConstraint(['usuario_creador_id'], ['usuarios.id'], name='fk_presupuestos_usuario_creador_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('presupuestos', schema=None) as batch_op:
        batch_op.create_index('ix_presupuestos_estado', ['estado'], unique=False)
        batch_op.create_index('ix_presupuestos_cliente_nombre', ['cliente_nombre'], unique=False)
        batch_op.create_index('ix_presupuestos_cliente_cuit', ['cliente_cuit'], unique=False)
        batch_op.create_index('ix_presupuestos_cliente_telefono', ['cliente_telefono'], unique=False)

    op.create_table(
        'detalles_presupuesto',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('presupuesto_id', sa.Integer(), nullable=False),
        sa.Column('producto_id', sa.Integer(), nullable=True),
        sa.Column('cod_interno', sa.String(length=50), nullable=True),
        sa.Column('descripcion', sa.String(length=300), nullable=False),
        sa.Column('cantidad', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('precio_unitario', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['presupuesto_id'], ['presupuestos.id'], name='fk_detalles_presupuesto_presupuesto_id'),
        sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], name='fk_detalles_presupuesto_producto_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('detalles_presupuesto', schema=None) as batch_op:
        batch_op.create_index('ix_detalles_presupuesto_presupuesto_id', ['presupuesto_id'], unique=False)


def downgrade():
    with op.batch_alter_table('detalles_presupuesto', schema=None) as batch_op:
        batch_op.drop_index('ix_detalles_presupuesto_presupuesto_id')
    op.drop_table('detalles_presupuesto')

    with op.batch_alter_table('presupuestos', schema=None) as batch_op:
        batch_op.drop_index('ix_presupuestos_cliente_telefono')
        batch_op.drop_index('ix_presupuestos_cliente_cuit')
        batch_op.drop_index('ix_presupuestos_cliente_nombre')
        batch_op.drop_index('ix_presupuestos_estado')
    op.drop_table('presupuestos')
