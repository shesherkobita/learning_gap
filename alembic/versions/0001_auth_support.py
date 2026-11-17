"""Ensure core authentication schema and dashboard indexes exist."""
from alembic import op
import sqlalchemy as sa

revision = "0001_auth_support"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "student" in inspector.get_table_names():
        student_columns = {c["name"]: c for c in inspector.get_columns("student")}
        if "teacher_id" in student_columns and student_columns["teacher_id"]["nullable"] is False:
            op.alter_column("student", "teacher_id", existing_type=sa.BigInteger(), nullable=True)
    tables = set(inspector.get_table_names())
    if "teacher" not in tables:
        op.create_table("teacher",
            sa.Column("teacher_id", sa.BigInteger, primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(100), nullable=False), sa.Column("email", sa.String(255), nullable=False, unique=True),
            sa.Column("department", sa.String(100)))
    if "student" not in tables:
        op.create_table("student",
            sa.Column("student_id", sa.BigInteger, primary_key=True, autoincrement=True),
            sa.Column("teacher_id", sa.BigInteger, sa.ForeignKey("teacher.teacher_id"), nullable=True),
            sa.Column("name", sa.String(100), nullable=False), sa.Column("class", sa.String(50), nullable=False),
            sa.Column("email", sa.String(255), nullable=False, unique=True))
    if "user_account" not in tables:
        op.execute("CREATE TYPE user_role AS ENUM ('teacher', 'student')")
        op.create_table("user_account",
            sa.Column("user_id", sa.BigInteger, primary_key=True, autoincrement=True), sa.Column("email", sa.String(255), unique=True, nullable=False),
            sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("role", sa.Enum("teacher", "student", name="user_role", create_type=False), nullable=False),
            sa.Column("teacher_id", sa.BigInteger, sa.ForeignKey("teacher.teacher_id"), unique=True),
            sa.Column("student_id", sa.BigInteger, sa.ForeignKey("student.student_id"), unique=True),
            sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()), sa.Column("failed_logins", sa.SmallInteger, nullable=False, server_default="0"),
            sa.Column("last_login_at", sa.DateTime), sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))
    inspector = sa.inspect(bind)
    if "assessment" in inspector.get_table_names():
        names = {x["name"] for x in inspector.get_indexes("assessment")}
        if "idx_assessment_student" not in names: op.create_index("idx_assessment_student", "assessment", ["student_id"])

def downgrade():
    # Keep user and learning data intact when reverting this compatibility migration.
    pass
