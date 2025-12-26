"""Initial database schema for FastApp core tables"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', sa.String(), default='user'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'media',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String()),
        sa.Column('description', sa.String()),
        sa.Column('url', sa.String()),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'products',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), default='USD'),
    )

    op.create_table(
        'courses',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
    )

    op.create_table(
        'posts',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('like_count', sa.Integer(), default=0),
    )

def downgrade() -> None:
    op.drop_table('posts')
    op.drop_table('courses')
    op.drop_table('products')
    op.drop_table('media')
    op.drop_table('users')