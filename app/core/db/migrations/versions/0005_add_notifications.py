"""Add notifications table for in-app and email notifications"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0005_add_notifications'
down_revision = '0004_add_lms_progress'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('notification_type', sa.String(), nullable=False),  # inapp or email
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('read', sa.Boolean(), default=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_index('idx_notification_user', 'notifications', ['user_id'])
    op.create_index('idx_notification_type', 'notifications', ['notification_type'])

def downgrade() -> None:
    op.drop_index('idx_notification_type', table_name='notifications')
    op.drop_index('idx_notification_user', table_name='notifications')
    op.drop_table('notifications')
