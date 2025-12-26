"""Add multi-role support and role audit logging"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0012_multi_role_support'
down_revision = '0011_lms_comprehensive_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add roles column as array to users table
    op.add_column(
        'users',
        sa.Column(
            'roles',
            postgresql.ARRAY(sa.String()),
            default=['user']
        )
    )
    
    # Add role_version for JWT revocation support
    op.add_column(
        'users',
        sa.Column('role_version', sa.Integer(), default=1)
    )
    
    # Create role_audit_log table
    op.create_table(
        'role_audit_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('changed_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(), nullable=False),  # 'assign', 'revoke', 'bulk_update'
        sa.Column('previous_roles', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('new_roles', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Index('idx_role_audit_user', 'user_id'),
        sa.Index('idx_role_audit_changed_by', 'changed_by'),
        sa.Index('idx_role_audit_created', 'created_at')
    )
    
    # Migrate existing role data to roles array
    op.execute("""
        UPDATE users 
        SET roles = ARRAY[role], role_version = 1 
        WHERE roles IS NULL
    """)
    
    # Make roles column non-nullable after migration
    op.alter_column('users', 'roles', nullable=False)
    
    # Add indexes for performance
    op.execute("CREATE INDEX idx_users_roles ON users USING gin (roles)")

def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_users_roles', table_name='users')
    op.drop_index('idx_role_audit_created', table_name='role_audit_log')
    op.drop_index('idx_role_audit_changed_by', table_name='role_audit_log')
    op.drop_index('idx_role_audit_user', table_name='role_audit_log')
    
    # Drop role_audit_log table
    op.drop_table('role_audit_log')
    
    # Drop new columns
    op.drop_column('users', 'role_version')
    op.drop_column('users', 'roles')
