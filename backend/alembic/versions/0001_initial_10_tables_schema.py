"""Initial 10 tables standardized schema for NEU Attendance

Revision ID: 0001_initial_10_tables
Revises: 
Create Date: 2026-11-03 04:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_10_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table: users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column(
            "role",
            sa.Enum("LECTURER", "STUDENT", "ADMIN", name="userrole"),
            nullable=False,
        ),
        sa.Column("microsoft_id", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_microsoft_id"), "users", ["microsoft_id"], unique=True)

    # 2. Table: subject_folders
    op.create_table(
        "subject_folders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lecturer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("folder_name", sa.String(length=255), nullable=False),
        sa.Column("semester", sa.String(length=100), nullable=False, server_default="HK1 2026-2027"),
        sa.Column("color_tag", sa.String(length=50), nullable=True, server_default="#003366"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["lecturer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "lecturer_id",
            "folder_name",
            "semester",
            name="uq_lecturer_folder_semester",
        ),
    )
    op.create_index(
        op.f("ix_subject_folders_lecturer_id"),
        "subject_folders",
        ["lecturer_id"],
        unique=False,
    )

    # 3. Table: students
    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_code", sa.String(length=20), nullable=False),
        sa.Column("last_name", sa.String(length=150), nullable=True, server_default=""),
        sa.Column("first_name", sa.String(length=100), nullable=True, server_default=""),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("date_of_birth", sa.String(length=50), nullable=True, server_default=""),
        sa.Column("admin_class", sa.String(length=100), nullable=True, server_default=""),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_students_student_code"), "students", ["student_code"], unique=True)
    op.create_index(op.f("ix_students_user_id"), "students", ["user_id"], unique=False)

    # 4. Table: buildings
    op.create_table(
        "buildings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("radius_meters", sa.Integer(), nullable=False, server_default="70"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_buildings_code"), "buildings", ["code"], unique=True)

    # 5. Table: courses
    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("folder_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("course_code", sa.String(length=100), nullable=False),
        sa.Column("course_name", sa.String(length=255), nullable=False),
        sa.Column("class_section", sa.String(length=100), nullable=True),
        sa.Column("room_name", sa.String(length=100), nullable=True),
        sa.Column("date_range_text", sa.String(length=255), nullable=True),
        sa.Column("schedule_text", sa.String(length=500), nullable=True),
        sa.Column("footer_date_text", sa.String(length=255), nullable=True),
        sa.Column("building_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lecturer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_binary", sa.LargeBinary(), nullable=True),
        sa.Column("template_filename", sa.String(length=255), nullable=True),
        sa.Column("total_sessions", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["folder_id"], ["subject_folders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lecturer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_courses_folder_id"), "courses", ["folder_id"], unique=False)
    op.create_index(op.f("ix_courses_lecturer_id"), "courses", ["lecturer_id"], unique=False)

    # 6. Table: enrollments
    op.create_table(
        "enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ordinal_number", sa.Integer(), nullable=False),
        sa.Column("sheet_name", sa.String(length=100), nullable=True),
        sa.Column("excel_row_index", sa.Integer(), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "student_id", name="uq_enrollment_course_student"),
    )
    op.create_index(op.f("ix_enrollments_course_id"), "enrollments", ["course_id"], unique=False)
    op.create_index(op.f("ix_enrollments_student_id"), "enrollments", ["student_id"], unique=False)

    # 7. Table: attendance_sessions
    op.create_table(
        "attendance_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_number", sa.Integer(), nullable=False),
        sa.Column("building_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "OPEN", "CLOSED", name="sessionstatus"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("require_audio", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("audio_tolerance_hz", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "session_number", name="uq_session_course_number"),
    )
    op.create_index(
        op.f("ix_attendance_sessions_course_id"),
        "attendance_sessions",
        ["course_id"],
        unique=False,
    )

    # 8. Table: qr_tokens
    op.create_table(
        "qr_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("pin_code", sa.String(length=10), nullable=False),
        sa.Column("audio_freq_hz", sa.Integer(), nullable=False, server_default="18500"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["attendance_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_qr_tokens_pin_code"), "qr_tokens", ["pin_code"], unique=True)
    op.create_index(op.f("ix_qr_tokens_session_id"), "qr_tokens", ["session_id"], unique=False)

    # 9. Table: attendance_records
    op.create_table(
        "attendance_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ATTENDED", "ABSENT", "PENDING_APPROVAL", name="attendancestatus"),
            nullable=False,
        ),
        sa.Column("marked_at", sa.DateTime(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("gps_accuracy_meters", sa.Float(), nullable=True),
        sa.Column("distance_meters", sa.Float(), nullable=True),
        sa.Column("detected_freq_hz", sa.Integer(), nullable=True),
        sa.Column("audio_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "method",
            sa.Enum("QR", "PIN_ANONYMOUS", "MANUAL", "EXCEL_IMPORT", name="attendancemethod"),
            nullable=True,
        ),
        sa.Column("device_fingerprint", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("updated_by_lecturer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["attendance_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_lecturer_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "student_id", name="uq_attendance_session_student"),
    )
    op.create_index(
        op.f("ix_attendance_records_session_id"),
        "attendance_records",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attendance_records_student_id"),
        "attendance_records",
        ["student_id"],
        unique=False,
    )

    # 10. Table: audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("details", sa.String(length=2000), nullable=True),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_attendance_records_student_id"), table_name="attendance_records")
    op.drop_index(op.f("ix_attendance_records_session_id"), table_name="attendance_records")
    op.drop_table("attendance_records")

    op.drop_index(op.f("ix_qr_tokens_session_id"), table_name="qr_tokens")
    op.drop_index(op.f("ix_qr_tokens_pin_code"), table_name="qr_tokens")
    op.drop_table("qr_tokens")

    op.drop_index(op.f("ix_attendance_sessions_course_id"), table_name="attendance_sessions")
    op.drop_table("attendance_sessions")

    op.drop_index(op.f("ix_enrollments_student_id"), table_name="enrollments")
    op.drop_index(op.f("ix_enrollments_course_id"), table_name="enrollments")
    op.drop_table("enrollments")

    op.drop_index(op.f("ix_courses_lecturer_id"), table_name="courses")
    op.drop_index(op.f("ix_courses_folder_id"), table_name="courses")
    op.drop_table("courses")

    op.drop_index(op.f("ix_buildings_code"), table_name="buildings")
    op.drop_table("buildings")

    op.drop_index(op.f("ix_students_user_id"), table_name="students")
    op.drop_index(op.f("ix_students_student_code"), table_name="students")
    op.drop_table("students")

    op.drop_index(op.f("ix_subject_folders_lecturer_id"), table_name="subject_folders")
    op.drop_table("subject_folders")

    op.drop_index(op.f("ix_users_microsoft_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    sa.Enum(name="attendancemethod").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="attendancestatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="sessionstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
