"""Seed demo users, courses, products, and notifications for development environment"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006_seed_initial_data'
down_revision = '0005_add_notifications'
branch_labels = None
depends_on = None

def upgrade() -> None:
    connection = op.get_bind()

    # Seed demo users
    connection.execute(sa.text("""
        INSERT INTO users (email, password_hash, role) VALUES
        ('admin@fastapp.dev', 'argon2hash-placeholder', 'admin'),
        ('user@fastapp.dev', 'argon2hash-placeholder', 'user');
    """))

    # Seed demo products
    connection.execute(sa.text("""
        INSERT INTO products (id, name, price, currency) VALUES
        ('p1', 'FastApp T-Shirt', 25.00, 'USD'),
        ('p2', 'Developer Mug', 15.00, 'USD'),
        ('p3', 'MonsterUI Sticker Pack', 10.00, 'USD');
    """))

    # Seed demo courses
    connection.execute(sa.text("""
        INSERT INTO courses (id, title, description) VALUES
        ('c1', 'Intro to FastHTML', 'Build powerful web apps using FastHTML.'),
        ('c2', 'HTMX for Developers', 'Reactive UIs with minimal JavaScript.'),
        ('c3', 'MonsterUI Design System', 'Learn to design sleek components.');
    """))

    # Seed demo notifications
    connection.execute(sa.text("""
        INSERT INTO notifications (user_id, notification_type, message, read) VALUES
        (1, 'inapp', 'Welcome to FastApp Admin Dashboard!', FALSE),
        (2, 'email', 'Thanks for signing up to FastApp!', FALSE);
    """))

def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM notifications;"))
    connection.execute(sa.text("DELETE FROM courses;"))
    connection.execute(sa.text("DELETE FROM products;"))
    connection.execute(sa.text("DELETE FROM users;"))