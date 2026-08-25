"""arreglo pagos de clientes
 
Revision ID: 69ce0446c89a
Revises: df1989e01d63
Create Date: 2026-08-24 21:19:05.196762
 
"""
from alembic import op
import sqlalchemy as sa
 
 
# revision identifiers, used by Alembic.
revision = '69ce0446c89a'
down_revision = 'df1989e01d63'
branch_labels = None
depends_on = None
 
 
def upgrade():
    # Migración vaciada a propósito: el contenido autogenerado original solo
    # capturaba drift preexistente de FKs/uniques faltantes en todo el esquema
    # (no relacionado a "pagos de clientes"), que se está resolviendo aparte,
    # tabla por tabla, de forma manual y controlada. No hay nada que ejecutar.
    pass
 
 
def downgrade():
    pass