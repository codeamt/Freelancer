"""Comprehensive LMS schema with courses, lessons, enrollments, progress, assessments, and certificates"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0011_lms_comprehensive_schema'
down_revision = '0010_finalize_indexes'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Drop old course_progress table if it exists (from migration 0004)
    op.execute("DROP TABLE IF EXISTS course_progress CASCADE")
    
    # Drop old courses table to recreate with new schema
    op.execute("DROP TABLE IF EXISTS courses CASCADE")
    
    # Create courses table with comprehensive schema
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('instructor_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('thumbnail_url', sa.String()),
        sa.Column('price', sa.Float(), default=0.0),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('duration_hours', sa.Float()),
        sa.Column('difficulty', sa.Enum('BEGINNER', 'INTERMEDIATE', 'ADVANCED', name='coursedifficulty'), default='BEGINNER'),
        sa.Column('status', sa.Enum('DRAFT', 'PUBLISHED', 'ARCHIVED', name='coursestatus'), default='DRAFT'),
        sa.Column('category', sa.String()),
        sa.Column('tags', postgresql.JSONB()),
        sa.Column('requirements', postgresql.JSONB()),
        sa.Column('learning_objectives', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create lessons table
    op.create_table(
        'lessons',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('content', sa.Text()),
        sa.Column('video_url', sa.String()),
        sa.Column('duration_minutes', sa.Integer()),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('lesson_type', sa.Enum('VIDEO', 'TEXT', 'QUIZ', 'ASSIGNMENT', name='lessontype'), default='VIDEO'),
        sa.Column('is_preview', sa.Boolean(), default=False),
        sa.Column('resources', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create enrollments table
    op.create_table(
        'enrollments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'COMPLETED', 'DROPPED', 'EXPIRED', name='enrollmentstatus'), default='ACTIVE'),
        sa.Column('enrolled_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('payment_id', sa.String()),
    )
    
    # Create progress table
    op.create_table(
        'progress',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('enrollment_id', sa.Integer(), sa.ForeignKey('enrollments.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('completed_lessons', postgresql.JSONB(), default=[]),
        sa.Column('progress_percent', sa.Float(), default=0.0),
        sa.Column('last_lesson_id', sa.Integer(), sa.ForeignKey('lessons.id')),
        sa.Column('time_spent_minutes', sa.Integer(), default=0),
        sa.Column('last_accessed', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create assessments table
    op.create_table(
        'assessments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('assessment_type', sa.Enum('QUIZ', 'EXAM', 'ASSIGNMENT', name='assessmenttype'), default='QUIZ'),
        sa.Column('questions', postgresql.JSONB()),
        sa.Column('passing_score', sa.Float(), default=70.0),
        sa.Column('time_limit_minutes', sa.Integer()),
        sa.Column('max_attempts', sa.Integer(), default=3),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    # Create assessment_submissions table
    op.create_table(
        'assessment_submissions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('assessment_id', sa.Integer(), sa.ForeignKey('assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('answers', postgresql.JSONB()),
        sa.Column('score', sa.Float()),
        sa.Column('passed', sa.Boolean(), default=False),
        sa.Column('attempt_number', sa.Integer(), default=1),
        sa.Column('submitted_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('graded_at', sa.DateTime()),
        sa.Column('feedback', sa.Text()),
    )
    
    # Create certificates table
    op.create_table(
        'certificates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('certificate_url', sa.String()),
        sa.Column('issued_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('verification_code', sa.String(), unique=True),
    )
    
    # Create indexes for better query performance
    op.create_index('idx_courses_instructor', 'courses', ['instructor_id'])
    op.create_index('idx_courses_status', 'courses', ['status'])
    op.create_index('idx_courses_category', 'courses', ['category'])
    
    op.create_index('idx_lessons_course', 'lessons', ['course_id'])
    op.create_index('idx_lessons_order', 'lessons', ['course_id', 'order'])
    
    op.create_index('idx_enrollments_user', 'enrollments', ['user_id'])
    op.create_index('idx_enrollments_course', 'enrollments', ['course_id'])
    op.create_index('idx_enrollments_user_course', 'enrollments', ['user_id', 'course_id'], unique=True)
    
    op.create_index('idx_progress_enrollment', 'progress', ['enrollment_id'])
    
    op.create_index('idx_assessments_course', 'assessments', ['course_id'])
    
    op.create_index('idx_submissions_assessment', 'assessment_submissions', ['assessment_id'])
    op.create_index('idx_submissions_user', 'assessment_submissions', ['user_id'])
    
    op.create_index('idx_certificates_user', 'certificates', ['user_id'])
    op.create_index('idx_certificates_course', 'certificates', ['course_id'])
    op.create_index('idx_certificates_verification', 'certificates', ['verification_code'])

def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_certificates_verification', table_name='certificates')
    op.drop_index('idx_certificates_course', table_name='certificates')
    op.drop_index('idx_certificates_user', table_name='certificates')
    
    op.drop_index('idx_submissions_user', table_name='assessment_submissions')
    op.drop_index('idx_submissions_assessment', table_name='assessment_submissions')
    
    op.drop_index('idx_assessments_course', table_name='assessments')
    
    op.drop_index('idx_progress_enrollment', table_name='progress')
    
    op.drop_index('idx_enrollments_user_course', table_name='enrollments')
    op.drop_index('idx_enrollments_course', table_name='enrollments')
    op.drop_index('idx_enrollments_user', table_name='enrollments')
    
    op.drop_index('idx_lessons_order', table_name='lessons')
    op.drop_index('idx_lessons_course', table_name='lessons')
    
    op.drop_index('idx_courses_category', table_name='courses')
    op.drop_index('idx_courses_status', table_name='courses')
    op.drop_index('idx_courses_instructor', table_name='courses')
    
    # Drop tables
    op.drop_table('certificates')
    op.drop_table('assessment_submissions')
    op.drop_table('assessments')
    op.drop_table('progress')
    op.drop_table('enrollments')
    op.drop_table('lessons')
    op.drop_table('courses')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS assessmenttype')
    op.execute('DROP TYPE IF EXISTS enrollmentstatus')
    op.execute('DROP TYPE IF EXISTS lessontype')
    op.execute('DROP TYPE IF EXISTS coursestatus')
    op.execute('DROP TYPE IF EXISTS coursedifficulty')
