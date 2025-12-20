"""Add recommendation logs to support GraphQL-based hybrid recommendations"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0003_add_recommendation_logs'
down_revision = '0002_add_analytics_tables'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'recommendation_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('recommended_type', sa.String(), nullable=False),  # product or course
        sa.Column('recommended_id', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_index('idx_recommendation_user', 'recommendation_logs', ['user_id'])
    op.create_index('idx_recommendation_type', 'recommendation_logs', ['recommended_type'])

def downgrade() -> None:
    op.drop_index('idx_recommendation_type', table_name='recommendation_logs')
    op.drop_index('idx_recommendation_user', table_name='recommendation_logs')
    op.drop_table('recommendation_logs')
