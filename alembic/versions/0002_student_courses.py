"""Add student course browsing, enrollment, and course request records."""
from alembic import op
import sqlalchemy as sa

revision = "0002_student_courses"
down_revision = "0001_auth_support"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "course",
        sa.Column("course_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("teacher_id", sa.BigInteger, sa.ForeignKey("teacher.teacher_id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("department", sa.String(100), nullable=False),
        sa.Column("target_class", sa.String(50)),
        sa.Column("is_published", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint("teacher_id", "title", name="uq_course_teacher_title"),
    )
    op.create_index("idx_course_published", "course", ["is_published", "department"])
    op.create_table(
        "course_enrollment",
        sa.Column("enrollment_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("course_id", sa.BigInteger, sa.ForeignKey("course.course_id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.BigInteger, sa.ForeignKey("student.student_id", ondelete="CASCADE"), nullable=False),
        sa.Column("enrolled_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint("course_id", "student_id", name="uq_course_student_enrollment"),
    )
    op.create_index("idx_enrollment_student", "course_enrollment", ["student_id"])
    op.create_table(
        "course_request",
        sa.Column("request_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.BigInteger, sa.ForeignKey("student.student_id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("department", sa.String(100), nullable=False),
        sa.Column("target_class", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("reason", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.CheckConstraint("status IN ('pending','approved','rejected')", name="ck_course_request_status"),
    )
    op.create_index("idx_course_request_student", "course_request", ["student_id", "created_at"])

    # Small development catalog so a fresh project has courses to browse.
    op.execute("""
      INSERT INTO course (teacher_id,title,description,department,target_class,is_published)
      SELECT t.teacher_id, seed.title, seed.description, seed.department, seed.target_class, TRUE
      FROM (VALUES
        ('farhana.karim@school.edu.bd','Fraction Foundations','Build confidence comparing, adding, and subtracting fractions using visual models and clear steps.','Mathematics','Class 8'),
        ('farhana.karim@school.edu.bd','Linear Equations Made Clear','Learn to solve one-variable equations and check each solution with substitution.','Mathematics','Class 8'),
        ('farhana.karim@school.edu.bd','Perimeter and Area','Understand when to measure a boundary and when to measure the space inside a shape.','Mathematics','Class 8'),
        ('sabbir.ahmed@school.edu.bd','Algebra Skills','Practice core algebra skills and build confidence solving equations step by step.','Mathematics','Class 9'),
        ('sabbir.ahmed@school.edu.bd','Geometry Essentials','Explore shapes, measurements, perimeter, and area through guided examples.','Mathematics','Class 9')
      ) AS seed(teacher_email,title,description,department,target_class)
      JOIN teacher t ON t.email=seed.teacher_email
      ON CONFLICT (teacher_id,title) DO NOTHING
    """)

def downgrade():
    op.drop_table("course_request")
    op.drop_index("idx_enrollment_student", table_name="course_enrollment")
    op.drop_table("course_enrollment")
    op.drop_index("idx_course_published", table_name="course")
    op.drop_table("course")
