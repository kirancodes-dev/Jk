"""stage6_hei_collaboration_lifecycle

Revision ID: a58f3d9c21e7
Revises: e49219c1a0f2
Create Date: 2026-09-23 11:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a58f3d9c21e7'
down_revision: Union[str, Sequence[str], None] = 'e49219c1a0f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. Expand PostgreSQL native enum milestonestatus
    if dialect == "postgresql":
        try:
            op.execute(sa.text("ALTER TYPE milestonestatus ADD VALUE IF NOT EXISTS 'REVISION_REQUESTED'"))
        except Exception:
            pass

    # 2. Universities: verified capability profile fields
    if "universities" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("universities")]
        with op.batch_alter_table("universities", schema=None) as batch_op:
            if "organization_profile_id" not in existing_cols:
                batch_op.add_column(sa.Column("organization_profile_id", sa.Integer(), sa.ForeignKey("organization_profiles.id", name="fk_universities_org_profile"), nullable=True))
            if "is_active" not in existing_cols:
                batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))
            if "capacity_max_active_projects" not in existing_cols:
                batch_op.add_column(sa.Column("capacity_max_active_projects", sa.Integer(), nullable=False, server_default="10"))
            if "version" not in existing_cols:
                batch_op.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

    # 3. University facilities / district coverage / capability evidence
    if "university_facilities" not in existing_tables:
        op.create_table(
            "university_facilities",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("facility_type", sa.String(50), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("capacity_units", sa.Integer(), nullable=True),
            sa.Column("is_operational", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        )

    if "university_district_coverage" not in existing_tables:
        op.create_table(
            "university_district_coverage",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("district_name", sa.String(100), nullable=False, index=True),
            sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        )

    if "university_capability_evidence" not in existing_tables:
        op.create_table(
            "university_capability_evidence",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("evidence_type", sa.String(50), nullable=False, server_default="OTHER"),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("evidence_object_id", sa.String(64), nullable=True, index=True),
            sa.Column("issued_by", sa.String(255), nullable=True),
            sa.Column("valid_until", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        )

    # 4. Team invitations
    if "team_invitations" not in existing_tables:
        op.create_table(
            "team_invitations",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("invited_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=True, index=True),
            sa.Column("faculty_id", sa.Integer(), sa.ForeignKey("faculty.id"), nullable=True, index=True),
            sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
            sa.Column("role_in_team", sa.String(100), server_default="Researcher & Developer", nullable=True),
            sa.Column("proposed_start_date", sa.DateTime(), nullable=True),
            sa.Column("proposed_end_date", sa.DateTime(), nullable=True),
            sa.Column("status", sa.String(50), server_default="PENDING", nullable=False, index=True),
            sa.Column("conflict_declared", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("conflict_notes", sa.Text(), nullable=True),
            sa.Column("response_notes", sa.Text(), nullable=True),
            sa.Column("responded_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        )

    # 5. Project members: cross-department, conflict, dates, lifecycle
    if "project_members" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("project_members")]
        with op.batch_alter_table("project_members", schema=None) as batch_op:
            if "department_id" not in existing_cols:
                batch_op.add_column(sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id", name="fk_project_members_department"), nullable=True))
            if "invitation_id" not in existing_cols:
                batch_op.add_column(sa.Column("invitation_id", sa.Integer(), sa.ForeignKey("team_invitations.id", name="fk_project_members_invitation"), nullable=True))
            if "start_date" not in existing_cols:
                batch_op.add_column(sa.Column("start_date", sa.DateTime(), nullable=True))
            if "end_date" not in existing_cols:
                batch_op.add_column(sa.Column("end_date", sa.DateTime(), nullable=True))
            if "conflict_declared" not in existing_cols:
                batch_op.add_column(sa.Column("conflict_declared", sa.Boolean(), nullable=False, server_default="false"))
            if "conflict_notes" not in existing_cols:
                batch_op.add_column(sa.Column("conflict_notes", sa.Text(), nullable=True))
            if "is_active" not in existing_cols:
                batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))

    # 6. Project membership history (immutable audit of add/remove/replace)
    if "project_membership_history" not in existing_tables:
        op.create_table(
            "project_membership_history",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=True),
            sa.Column("faculty_id", sa.Integer(), sa.ForeignKey("faculty.id"), nullable=True),
            sa.Column("action", sa.String(50), nullable=False),
            sa.Column("previous_member_student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=True),
            sa.Column("role_in_team", sa.String(100), nullable=True),
            sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("occurred_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        )

    # 7. Projects: milestone lock + mentor acceptance state
    if "projects" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("projects")]
        with op.batch_alter_table("projects", schema=None) as batch_op:
            if "milestones_locked" not in existing_cols:
                batch_op.add_column(sa.Column("milestones_locked", sa.Boolean(), nullable=False, server_default="false"))
            if "faculty_mentor_status" not in existing_cols:
                batch_op.add_column(sa.Column("faculty_mentor_status", sa.String(50), nullable=False, server_default="PENDING"))

    # 8. Project milestones: reviewer + review notes
    if "project_milestones" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("project_milestones")]
        with op.batch_alter_table("project_milestones", schema=None) as batch_op:
            if "reviewed_by_user_id" not in existing_cols:
                batch_op.add_column(sa.Column("reviewed_by_user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_milestones_reviewed_by"), nullable=True))
            if "review_notes" not in existing_cols:
                batch_op.add_column(sa.Column("review_notes", sa.Text(), nullable=True))

    # 9. Project tasks: milestone linkage + typed status
    if "project_tasks" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("project_tasks")]
        with op.batch_alter_table("project_tasks", schema=None) as batch_op:
            if "milestone_id" not in existing_cols:
                batch_op.add_column(sa.Column("milestone_id", sa.Integer(), sa.ForeignKey("project_milestones.id", name="fk_tasks_milestone"), nullable=True))
            if "status" not in existing_cols:
                batch_op.add_column(sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"))

    # 10. Solution proposals: versioned government/HEI/industry workflow
    if "solution_proposals" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("solution_proposals")]
        with op.batch_alter_table("solution_proposals", schema=None) as batch_op:
            if "objectives" not in existing_cols:
                batch_op.add_column(sa.Column("objectives", sa.Text(), nullable=True))
            if "feasibility_notes" not in existing_cols:
                batch_op.add_column(sa.Column("feasibility_notes", sa.Text(), nullable=True))
            if "budget_breakdown" not in existing_cols:
                batch_op.add_column(sa.Column("budget_breakdown", sa.Text(), nullable=True))
            if "risks" not in existing_cols:
                batch_op.add_column(sa.Column("risks", sa.Text(), nullable=True))
            if "safeguarding_notes" not in existing_cols:
                batch_op.add_column(sa.Column("safeguarding_notes", sa.Text(), nullable=True))
            if "maintenance_plan" not in existing_cols:
                batch_op.add_column(sa.Column("maintenance_plan", sa.Text(), nullable=True))
            if "measurable_outcomes" not in existing_cols:
                batch_op.add_column(sa.Column("measurable_outcomes", sa.Text(), nullable=True))
            if "status" not in existing_cols:
                batch_op.add_column(sa.Column("status", sa.String(50), nullable=False, server_default="DRAFT"))
            if "version" not in existing_cols:
                batch_op.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
            if "supersedes_id" not in existing_cols:
                batch_op.add_column(sa.Column("supersedes_id", sa.Integer(), sa.ForeignKey("solution_proposals.id", name="fk_proposal_supersedes"), nullable=True))
            if "is_current" not in existing_cols:
                batch_op.add_column(sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"))
            if "submitted_by_user_id" not in existing_cols:
                batch_op.add_column(sa.Column("submitted_by_user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_proposal_submitted_by"), nullable=True))
            if "faculty_reviewed_by_id" not in existing_cols:
                batch_op.add_column(sa.Column("faculty_reviewed_by_id", sa.Integer(), sa.ForeignKey("faculty.id", name="fk_proposal_faculty_reviewer"), nullable=True))
            if "faculty_review_notes" not in existing_cols:
                batch_op.add_column(sa.Column("faculty_review_notes", sa.Text(), nullable=True))
            if "hei_approved_by_user_id" not in existing_cols:
                batch_op.add_column(sa.Column("hei_approved_by_user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_proposal_hei_approver"), nullable=True))
            if "hei_approval_notes" not in existing_cols:
                batch_op.add_column(sa.Column("hei_approval_notes", sa.Text(), nullable=True))
            if "government_reviewed_by_user_id" not in existing_cols:
                batch_op.add_column(sa.Column("government_reviewed_by_user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_proposal_gov_reviewer"), nullable=True))
            if "government_review_notes" not in existing_cols:
                batch_op.add_column(sa.Column("government_review_notes", sa.Text(), nullable=True))
            if "revision_requested_reason" not in existing_cols:
                batch_op.add_column(sa.Column("revision_requested_reason", sa.Text(), nullable=True))
            if "updated_at" not in existing_cols:
                batch_op.add_column(sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True))

        # Backfill legacy rows to a coherent status
        op.execute(sa.text(
            "UPDATE solution_proposals SET status = CASE WHEN is_approved_by_gov = :true_val THEN 'APPROVED' ELSE 'SUBMITTED' END "
            "WHERE status IS NULL OR status = 'DRAFT'"
        ).bindparams(true_val=True if dialect != "sqlite" else 1))

    # 11. Project documents: server-generated evidence reference
    if "project_documents" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("project_documents")]
        with op.batch_alter_table("project_documents", schema=None) as batch_op:
            if "evidence_object_id" not in existing_cols:
                batch_op.add_column(sa.Column("evidence_object_id", sa.String(64), nullable=True))
            if "uploaded_by_user_id" not in existing_cols:
                batch_op.add_column(sa.Column("uploaded_by_user_id", sa.Integer(), sa.ForeignKey("users.id", name="fk_documents_uploaded_by"), nullable=True))

    # 12. Review comments (proposals, milestones, deliverables, tasks)
    if "review_comments" not in existing_tables:
        op.create_table(
            "review_comments",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("entity_type", sa.String(50), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=False, index=True),
            sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        )

    # 13. Evidence files: typed, versioned, checksum-verified evidence substrate
    if "evidence_files" not in existing_tables:
        op.create_table(
            "evidence_files",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column("object_id", sa.String(64), unique=True, nullable=False, index=True),
            sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("entity_type", sa.String(50), nullable=False, index=True),
            sa.Column("entity_id", sa.Integer(), nullable=False, index=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("version", sa.Integer(), server_default="1", nullable=False),
            sa.Column("is_current", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("supersedes_id", sa.Integer(), sa.ForeignKey("evidence_files.id"), nullable=True),
            sa.Column("original_filename", sa.String(255), nullable=False),
            sa.Column("detected_mime", sa.String(100), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("sha256_checksum", sa.String(64), nullable=False),
            sa.Column("storage_key", sa.String(500), nullable=False),
            sa.Column("scan_status", sa.String(50), server_default="CLEAN", nullable=True),
            sa.Column("access_classification", sa.String(50), server_default="RESTRICTED", nullable=True),
            sa.Column("review_status", sa.String(50), server_default="PENDING", nullable=False, index=True),
            sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("review_notes", sa.Text(), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        )

    # 14. Backfill university <-> organization_profile linkage for existing VERIFIED HEIs
    if "universities" in existing_tables and "organization_profiles" in existing_tables:
        op.execute(sa.text(
            "UPDATE universities SET organization_profile_id = ("
            "  SELECT op.id FROM organization_profiles op "
            "  JOIN users u ON u.id = op.user_id "
            "  WHERE u.id = universities.user_id LIMIT 1"
            ") WHERE organization_profile_id IS NULL"
        ))


def downgrade() -> None:
    op.drop_table("evidence_files")
    op.drop_table("review_comments")
    with op.batch_alter_table("project_documents", schema=None) as batch_op:
        batch_op.drop_column("uploaded_by_user_id")
        batch_op.drop_column("evidence_object_id")
    with op.batch_alter_table("solution_proposals", schema=None) as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("revision_requested_reason")
        batch_op.drop_column("government_review_notes")
        batch_op.drop_column("government_reviewed_by_user_id")
        batch_op.drop_column("hei_approval_notes")
        batch_op.drop_column("hei_approved_by_user_id")
        batch_op.drop_column("faculty_review_notes")
        batch_op.drop_column("faculty_reviewed_by_id")
        batch_op.drop_column("submitted_by_user_id")
        batch_op.drop_column("is_current")
        batch_op.drop_column("supersedes_id")
        batch_op.drop_column("version")
        batch_op.drop_column("status")
        batch_op.drop_column("measurable_outcomes")
        batch_op.drop_column("maintenance_plan")
        batch_op.drop_column("safeguarding_notes")
        batch_op.drop_column("risks")
        batch_op.drop_column("budget_breakdown")
        batch_op.drop_column("feasibility_notes")
        batch_op.drop_column("objectives")
    with op.batch_alter_table("project_tasks", schema=None) as batch_op:
        batch_op.drop_column("status")
        batch_op.drop_column("milestone_id")
    with op.batch_alter_table("project_milestones", schema=None) as batch_op:
        batch_op.drop_column("review_notes")
        batch_op.drop_column("reviewed_by_user_id")
    with op.batch_alter_table("projects", schema=None) as batch_op:
        batch_op.drop_column("faculty_mentor_status")
        batch_op.drop_column("milestones_locked")
    op.drop_table("project_membership_history")
    with op.batch_alter_table("project_members", schema=None) as batch_op:
        batch_op.drop_column("is_active")
        batch_op.drop_column("conflict_notes")
        batch_op.drop_column("conflict_declared")
        batch_op.drop_column("end_date")
        batch_op.drop_column("start_date")
        batch_op.drop_column("invitation_id")
        batch_op.drop_column("department_id")
    op.drop_table("team_invitations")
    op.drop_table("university_capability_evidence")
    op.drop_table("university_district_coverage")
    op.drop_table("university_facilities")
    with op.batch_alter_table("universities", schema=None) as batch_op:
        batch_op.drop_column("version")
        batch_op.drop_column("capacity_max_active_projects")
        batch_op.drop_column("is_active")
        batch_op.drop_column("organization_profile_id")
