"""add game status field

Revision ID: 002
Revises: 001
Create Date: 2023-11-15 20:55:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Add status column with default value 'scheduled'
    op.add_column('game', sa.Column('status', sa.String(20), nullable=True))
    op.execute("UPDATE game SET status = 'scheduled' WHERE status IS NULL")
    op.alter_column('game', 'status', nullable=False, server_default='scheduled')

def downgrade():
    op.drop_column('game', 'status')
