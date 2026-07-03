"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2025-10-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('teams',
    sa.Column('team_name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('team_name')
    )
    
    op.create_table('users',
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('team_name', sa.String(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    sa.ForeignKeyConstraint(['team_name'], ['teams.team_name'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id')
    )
    
    op.create_table('pull_requests',
    sa.Column('pull_request_id', sa.String(), nullable=False),
    sa.Column('pull_request_name', sa.String(), nullable=False),
    sa.Column('author_id', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('assigned_reviewers', postgresql.ARRAY(sa.String()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('merged_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['users.user_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('pull_request_id')
    )

def downgrade() -> None:
    op.drop_table('pull_requests')
    op.drop_table('users')
    op.drop_table('teams')
