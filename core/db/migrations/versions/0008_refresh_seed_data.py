"""Reapply seed data after rollback for testing and development refresh"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0008_refresh_seed_data'
down_revision = '0007_rollback_seed_data'
branch_labels = None
depends_on = None

def upgrade() -> None:
    connection = op.get_bind()

    # Reinsert demo users (only if they don't exist)
    connection.execute(sa.text("""
        INSERT INTO users (email, password_hash, role) VALUES
        ('admin@fastapp.dev', 'argon2hash-placeholder', 'admin'),
        ('user@fastapp.dev', 'argon2hash-placeholder', 'user')
        ON CONFLICT (email) DO NOTHING;
    """))

    # Reinsert demo products
    connection.execute(sa.text("""
        INSERT INTO products (id, name, price, currency) VALUES
        ('p1', 'FastApp T-Shirt', 25.00, 'USD'),
        ('p2', 'Developer Mug', 15.00, 'USD'),
        ('p3', 'MonsterUI Sticker Pack', 10.00, 'USD')
        ON CONFLICT (id) DO NOTHING;
    """))

    # Reinsert demo courses
    connection.execute(sa.text("""
        INSERT INTO courses (id, title, description) VALUES
        ('c1', 'Intro to FastHTML', 'Build powerful web apps using FastHTML.'),
        ('c2', 'HTMX for Developers', 'Reactive UIs with minimal JavaScript.'),
        ('c3', 'MonsterUI Design System', 'Learn to design sleek components.')
        ON CONFLICT (id) DO NOTHING;
    """))

    # Reinsert demo notifications (only if users exist)
    connection.execute(sa.text("""
        INSERT INTO notifications (user_id, notification_type, message, read) 
        SELECT 1, 'inapp', 'Welcome back to FastApp Admin Dashboard!', FALSE
        WHERE EXISTS (SELECT 1 FROM users WHERE id = 1)
        ON CONFLICT DO NOTHING;
        
        INSERT INTO notifications (user_id, notification_type, message, read) 
        SELECT 2, 'email', 'Your FastApp demo data has been refreshed!', FALSE
        WHERE EXISTS (SELECT 1 FROM users WHERE id = 2)
        ON CONFLICT DO NOTHING;
    """))

def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM notifications WHERE message LIKE '%FastApp%';"))
    connection.execute(sa.text("DELETE FROM courses WHERE id IN ('c1','c2','c3');"))
    connection.execute(sa.text("DELETE FROM products WHERE id IN ('p1','p2','p3');"))
    connection.execute(sa.text("DELETE FROM users WHERE email IN ('admin@fastapp.dev','user@fastapp.dev');"))
