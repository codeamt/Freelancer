"""Remove seeded demo data while preserving schema integrity"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0007_rollback_seed_data'
down_revision = '0006_seed_initial_data'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # This upgrade does nothing; rollback is handled in downgrade.
    pass

def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM notifications WHERE message LIKE '%FastApp%';"))
    connection.execute(sa.text("DELETE FROM courses WHERE id IN ('c1','c2','c3');"))
    connection.execute(sa.text("DELETE FROM products WHERE id IN ('p1','p2','p3');"))
    connection.execute(sa.text("DELETE FROM users WHERE email IN ('admin@fastapp.dev','user@fastapp.dev');"))
