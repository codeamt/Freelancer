"""Add analytics and event tracking tables for FastApp"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002_add_analytics_tables'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'metrics',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('collected_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_index('idx_event_type', 'events', ['event_type'])
    op.create_index('idx_metric_name', 'metrics', ['metric_name'])

def downgrade() -> None:
    op.drop_index('idx_metric_name', table_name='metrics')
    op.drop_index('idx_event_type', table_name='events')
    op.drop_table('metrics')
    op.drop_table('events')