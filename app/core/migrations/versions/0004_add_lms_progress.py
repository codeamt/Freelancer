"""Add LMS progress tracking for user course and lesson completion"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0004_add_lms_progress'
down_revision = '0003_add_recommendation_logs'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'course_progress',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('course_id', sa.String(), sa.ForeignKey('courses.id', ondelete='CASCADE')),
        sa.Column('completed_lessons', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('progress_percent', sa.Float(), nullable=False, default=0.0),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('idx_progress_user', 'course_progress', ['user_id'])
    op.create_index('idx_progress_course', 'course_progress', ['course_id'])

def downgrade() -> None:
    op.drop_index('idx_progress_course', table_name='course_progress')
    op.drop_index('idx_progress_user', table_name='course_progress')
    op.drop_table('course_progress')