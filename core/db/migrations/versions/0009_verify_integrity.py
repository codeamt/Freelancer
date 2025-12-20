"""Add constraints and cleanup orphaned records to maintain referential integrity"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0009_verify_integrity'
down_revision = '0008_refresh_seed_data'
branch_labels = None
depends_on = None

def upgrade() -> None:
    connection = op.get_bind()

    # Cleanup orphaned records
    connection.execute(sa.text("""
        DELETE FROM media WHERE user_id NOT IN (SELECT id FROM users);
        DELETE FROM recommendation_logs WHERE user_id NOT IN (SELECT id FROM users);
        DELETE FROM course_progress WHERE user_id NOT IN (SELECT id FROM users);
        DELETE FROM notifications WHERE user_id NOT IN (SELECT id FROM users);
    """))

    # Ensure referential integrity with ON DELETE CASCADE constraints where missing
    with op.batch_alter_table('media') as batch_op:
        batch_op.create_foreign_key('fk_media_user_id', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('recommendation_logs') as batch_op:
        batch_op.create_foreign_key('fk_recommendations_user_id', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('course_progress') as batch_op:
        batch_op.create_foreign_key('fk_progress_user_id', 'users', ['user_id'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key('fk_progress_course_id', 'courses', ['course_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('notifications') as batch_op:
        batch_op.create_foreign_key('fk_notifications_user_id', 'users', ['user_id'], ['id'], ondelete='CASCADE')

def downgrade() -> None:
    with op.batch_alter_table('notifications') as batch_op:
        batch_op.drop_constraint('fk_notifications_user_id', type_='foreignkey')

    with op.batch_alter_table('course_progress') as batch_op:
        batch_op.drop_constraint('fk_progress_user_id', type_='foreignkey')
        batch_op.drop_constraint('fk_progress_course_id', type_='foreignkey')

    with op.batch_alter_table('recommendation_logs') as batch_op:
        batch_op.drop_constraint('fk_recommendations_user_id', type_='foreignkey')

    with op.batch_alter_table('media') as batch_op:
        batch_op.drop_constraint('fk_media_user_id', type_='foreignkey')
