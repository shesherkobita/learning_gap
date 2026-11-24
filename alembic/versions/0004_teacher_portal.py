"""Add teacher classes, scheduled assessments, submissions, and gradebook data."""
from alembic import op
import sqlalchemy as sa

revision = "0004_teacher_portal"
down_revision = "0003_learning_gaps_quizzes"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("course", sa.Column("syllabus", sa.Text, nullable=True))
    op.add_column("course", sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()))
    op.create_table(
        "course_material",
        sa.Column("material_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("course_id", sa.BigInteger, sa.ForeignKey("course.course_id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False), sa.Column("material_type", sa.String(40), nullable=False),
        sa.Column("resource_url", sa.String(1000), nullable=False), sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_table(
        "course_announcement",
        sa.Column("announcement_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("course_id", sa.BigInteger, sa.ForeignKey("course.course_id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False), sa.Column("body", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_table(
        "teacher_assessment",
        sa.Column("assessment_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("course_id", sa.BigInteger, sa.ForeignKey("course.course_id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False), sa.Column("description", sa.Text),
        sa.Column("kind", sa.String(20), nullable=False), sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("total_points", sa.Numeric(7,2), nullable=False, server_default="100"),
        sa.Column("rubric", sa.Text), sa.Column("is_published", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.CheckConstraint("kind IN ('quiz','assignment')", name="ck_teacher_assessment_kind"),
    )
    op.create_index("idx_teacher_assessment_course_due", "teacher_assessment", ["course_id", "due_at"])
    op.create_table(
        "teacher_assessment_question",
        sa.Column("question_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("assessment_id", sa.BigInteger, sa.ForeignKey("teacher_assessment.assessment_id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_text", sa.Text, nullable=False), sa.Column("answer_type", sa.String(20), nullable=False),
        sa.Column("choices", sa.Text), sa.Column("correct_answer", sa.Text),
        sa.Column("points", sa.Numeric(7,2), nullable=False, server_default="1"),
        sa.CheckConstraint("answer_type IN ('multiple_choice','short_answer')", name="ck_teacher_question_type"),
    )
    op.create_table(
        "teacher_submission",
        sa.Column("submission_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("assessment_id", sa.BigInteger, sa.ForeignKey("teacher_assessment.assessment_id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.BigInteger, sa.ForeignKey("student.student_id", ondelete="CASCADE"), nullable=False),
        sa.Column("answers", sa.Text, nullable=False), sa.Column("points_earned", sa.Numeric(7,2)),
        sa.Column("status", sa.String(20), nullable=False, server_default="submitted"), sa.Column("feedback", sa.Text),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("graded_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("assessment_id", "student_id", name="uq_teacher_submission_student"),
        sa.CheckConstraint("status IN ('submitted','graded')", name="ck_teacher_submission_status"),
    )
    op.create_index("idx_teacher_submission_assessment", "teacher_submission", ["assessment_id", "status"])
    op.create_table(
        "gradebook_weight",
        sa.Column("weight_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("course_id", sa.BigInteger, sa.ForeignKey("course.course_id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(80), nullable=False), sa.Column("weight_percent", sa.Numeric(5,2), nullable=False),
        sa.UniqueConstraint("course_id", "category", name="uq_gradebook_weight_category"),
        sa.CheckConstraint("weight_percent >= 0 AND weight_percent <= 100", name="ck_gradebook_weight_range"),
    )
    op.create_table(
        "gradebook_entry",
        sa.Column("entry_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("course_id", sa.BigInteger, sa.ForeignKey("course.course_id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.BigInteger, sa.ForeignKey("student.student_id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(80), nullable=False), sa.Column("item_name", sa.String(160), nullable=False),
        sa.Column("score", sa.Numeric(7,2), nullable=False), sa.Column("max_score", sa.Numeric(7,2), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint("course_id", "student_id", "category", "item_name", name="uq_gradebook_entry_item"),
        sa.CheckConstraint("max_score > 0 AND score >= 0 AND score <= max_score", name="ck_gradebook_entry_score"),
    )
    op.create_index("idx_gradebook_entry_course", "gradebook_entry", ["course_id", "student_id"])

def downgrade():
    op.drop_index("idx_gradebook_entry_course", table_name="gradebook_entry")
    op.drop_table("gradebook_entry")
    op.drop_table("gradebook_weight")
    op.drop_index("idx_teacher_submission_assessment", table_name="teacher_submission")
    op.drop_table("teacher_submission")
    op.drop_table("teacher_assessment_question")
    op.drop_index("idx_teacher_assessment_course_due", table_name="teacher_assessment")
    op.drop_table("teacher_assessment")
    op.drop_table("course_announcement")
    op.drop_table("course_material")
    op.drop_column("course", "updated_at")
    op.drop_column("course", "syllabus")
