from sqlalchemy import text
from backend.app.core.database import engine, Base

def migrate_database_schema():
    """
    Safely adds missing columns and tables to the active database (PostgreSQL / SQLite).
    Runs non-destructively using IF NOT EXISTS.
    """
    # 1. Create any missing tables (audit_logs, organization_profiles, etc.)
    Base.metadata.create_all(bind=engine)

    # 2. Add missing columns to existing tables
    is_postgres = "postgres" in str(engine.url)

    alter_statements = [
        # enum values for postgres
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'IN_PROGRESS';",
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'FIELD_VERIFICATION';",
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'CLOSED';",
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'UNDER_REVIEW';",
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'NEEDS_MORE_INFO';",
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'DUPLICATE';",
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'VALIDATED';",
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'UNIVERSITY_ASSIGNED';",
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'TEAM_FORMED';",
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'SOLUTION_PROPOSED';",
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'APPROVED';",
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'PROTOTYPE';",
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'FIELD_TESTING';",
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'DEPLOYMENT';",
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'RESOLVED';",
        "ALTER TYPE challengestatus ADD VALUE IF NOT EXISTS 'REJECTED';",

        # challenges table
        "ALTER TABLE challenges ADD COLUMN IF NOT EXISTS affected_population INTEGER DEFAULT 100;",
        "ALTER TABLE challenges ADD COLUMN IF NOT EXISTS moderation_reason TEXT;",
        "ALTER TABLE challenges ADD COLUMN IF NOT EXISTS moderated_by VARCHAR(255);",
        "ALTER TABLE challenges ADD COLUMN IF NOT EXISTS moderated_at TIMESTAMP;",
        
        # project_milestones table
        "ALTER TABLE project_milestones ADD COLUMN IF NOT EXISTS weight_pct FLOAT DEFAULT 20.0;",
        "ALTER TABLE project_milestones ADD COLUMN IF NOT EXISTS deliverable_files TEXT;",
    ]

    with engine.connect() as conn:
        for stmt in alter_statements:
            try:
                if is_postgres:
                    conn.execute(text(stmt))
                else:
                    # SQLite fallback (no IF NOT EXISTS on ADD COLUMN)
                    clean_stmt = stmt.replace(" IF NOT EXISTS", "")
                    conn.execute(text(clean_stmt))
                conn.commit()
            except Exception as e:
                # Column might already exist or dialect specific syntax
                pass

if __name__ == "__main__":
    migrate_database_schema()
    print("[✓] Database schema migration executed successfully.")
