"""Add saved quizzes and guided learning-plan progress."""
from alembic import op
import sqlalchemy as sa

revision = "0003_learning_gaps_quizzes"
down_revision = "0002_student_courses"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "quiz_attempt",
        sa.Column("attempt_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.BigInteger, sa.ForeignKey("student.student_id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", sa.BigInteger, sa.ForeignKey("topic.topic_id"), nullable=True),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("correct_count", sa.SmallInteger, nullable=False),
        sa.Column("question_count", sa.SmallInteger, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_quiz_attempt_student", "quiz_attempt", ["student_id", "created_at"])
    op.create_table(
        "quiz_answer",
        sa.Column("answer_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("attempt_id", sa.BigInteger, sa.ForeignKey("quiz_attempt.attempt_id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.BigInteger, sa.ForeignKey("question.question_id", ondelete="CASCADE"), nullable=False),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("is_correct", sa.Boolean, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint("attempt_id", "question_id", name="uq_quiz_answer_attempt_question"),
    )
    op.create_index("idx_quiz_answer_question", "quiz_answer", ["question_id"])
    op.create_table(
        "question_option",
        sa.Column("option_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("question_id", sa.BigInteger, sa.ForeignKey("question.question_id", ondelete="CASCADE"), nullable=False),
        sa.Column("option_text", sa.Text, nullable=False),
        sa.Column("is_correct", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.SmallInteger, nullable=False),
        sa.UniqueConstraint("question_id", "option_text", name="uq_question_option_text"),
    )
    op.create_index("idx_question_option_question", "question_option", ["question_id", "sort_order"])
    op.create_table(
        "lesson",
        sa.Column("lesson_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("topic_id", sa.BigInteger, sa.ForeignKey("topic.topic_id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("objective", sa.String(300), nullable=False),
        sa.Column("lesson_text", sa.Text, nullable=False),
        sa.Column("sort_order", sa.SmallInteger, nullable=False, server_default="1"),
        sa.UniqueConstraint("topic_id", "title", name="uq_lesson_topic_title"),
    )
    op.create_table(
        "student_lesson_progress",
        sa.Column("student_id", sa.BigInteger, sa.ForeignKey("student.student_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("lesson_id", sa.BigInteger, sa.ForeignKey("lesson.lesson_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("completed_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.execute("""
      INSERT INTO lesson(topic_id,title,objective,lesson_text,sort_order)
      SELECT t.topic_id, seed.title, seed.objective, seed.lesson_text, seed.sort_order
      FROM (VALUES
        ('Fractions','Find a common denominator','Rewrite fractions with the same denominator before adding.','To add fractions, first split each whole into the same size pieces. For 1/2 + 1/3, sixths work: 1/2 = 3/6 and 1/3 = 2/6, so the sum is 5/6. Add the numerators only after the denominators match.',1),
        ('Fractions','Compare unit fractions','Use equal-sized wholes or a number line to compare fractions.','When the numerator is 1, a larger denominator means each piece is smaller. Imagine the same pizza cut into 3 pieces or 5 pieces: one third is larger than one fifth. Place both fractions on a number line to check.',2),
        ('Linear Equations','Keep both sides balanced','Use inverse operations on both sides of an equation.','An equation is like a balanced scale. For 3x - 4 = 11, add 4 to both sides to get 3x = 15, then divide both sides by 3. So x = 5. Substitute 5 back into the original equation to check.',1),
        ('Linear Equations','Check signs when moving terms','Undo addition and subtraction without changing the equation balance.','Instead of moving a term across the equals sign and guessing its new sign, perform the inverse operation on both sides. Write each line so you can see the balance stay equal, then check by substitution.',2),
        ('Perimeter & Area','Tell perimeter and area apart','Recognize whether a problem asks for the boundary or the inside.','Perimeter measures the distance around a shape, like a fence. Area measures the space inside, like carpet. For a 5 cm by 3 cm rectangle, perimeter is 5 + 3 + 5 + 3 = 16 cm, while area is 5 × 3 = 15 square cm.',1),
        ('Perimeter & Area','Choose the right rectangle formula','Calculate perimeter and area using the correct units.','For a rectangle with length l and width w, perimeter is 2l + 2w and uses ordinary units such as cm. Area is l × w and uses square units such as cm². Before calculating, underline whether the question asks around or inside.',2)
      ) AS seed(topic_name,title,objective,lesson_text,sort_order)
      JOIN topic t ON t.topic_name=seed.topic_name
      ON CONFLICT (topic_id,title) DO NOTHING
    """)
    op.execute("""
      INSERT INTO question_option(question_id,option_text,is_correct,sort_order)
      SELECT q.question_id, choice.option_text, choice.option_text=q.correct_answer, choice.sort_order
      FROM question q
      CROSS JOIN LATERAL (VALUES
        (CASE WHEN q.question_text ILIKE 'Which is larger:%' THEN '1/3' WHEN q.correct_answer='5/6' THEN '5/6' WHEN q.correct_answer='5' THEN '5' ELSE q.correct_answer END,1),
        (CASE WHEN q.question_text ILIKE 'Which is larger:%' THEN '1/5' WHEN q.correct_answer='5/6' THEN '2/5' WHEN q.correct_answer='5' THEN '7/3' ELSE '15 cm' END,2),
        (CASE WHEN q.question_text ILIKE 'Which is larger:%' THEN '1/2' WHEN q.correct_answer='5/6' THEN '1/6' WHEN q.correct_answer='5' THEN '3' ELSE '8 cm' END,3)
      ) AS choice(option_text,sort_order)
      WHERE q.correct_answer IN ('5/6','5','16 cm','1/3')
      ON CONFLICT (question_id,option_text) DO NOTHING
    """)

def downgrade():
    op.drop_table("student_lesson_progress")
    op.drop_table("lesson")
    op.drop_index("idx_question_option_question", table_name="question_option")
    op.drop_table("question_option")
    op.drop_index("idx_quiz_answer_question", table_name="quiz_answer")
    op.drop_table("quiz_answer")
    op.drop_index("idx_quiz_attempt_student", table_name="quiz_attempt")
    op.drop_table("quiz_attempt")
