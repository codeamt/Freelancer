"""Add indexes to optimize frequently queried columns and joins across FastApp schema"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0010_finalize_indexes'
down_revision = '0009_verify_integrity'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Users: search and auth
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_role', 'users', ['role'])

    # Media: search by title and date
    op.create_index('idx_media_title', 'media', ['title'])
    op.create_index('idx_media_uploaded_at', 'media', ['uploaded_at'])

    # Products: name and price filters
    op.create_index('idx_products_name', 'products', ['name'])
    op.create_index('idx_products_price', 'products', ['price'])

    # Courses: title and description text search
    op.create_index('idx_courses_title', 'courses', ['title'])

    # Posts: content and like_count analytics
    op.create_index('idx_posts_like_count', 'posts', ['like_count'])

    # Recommendation logs: performance for GraphQL rec queries
    op.create_index('idx_recommendation_confidence', 'recommendation_logs', ['confidence'])

    # Course progress: partial completion lookups
    op.create_index('idx_progress_percent', 'course_progress', ['progress_percent'])

    # Notifications: read status filtering
    op.create_index('idx_notifications_read', 'notifications', ['read'])

def downgrade() -> None:
    op.drop_index('idx_notifications_read', table_name='notifications')
    op.drop_index('idx_progress_percent', table_name='course_progress')
    op.drop_index('idx_recommendation_confidence', table_name='recommendation_logs')
    op.drop_index('idx_posts_like_count', table_name='posts')
    op.drop_index('idx_courses_title', table_name='courses')
    op.drop_index('idx_products_price', table_name='products')
    op.drop_index('idx_products_name', table_name='products')
    op.drop_index('idx_media_uploaded_at', table_name='media')
    op.drop_index('idx_media_title', table_name='media')
    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
