import logging
from typing import Tuple, Optional
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.core.config import settings

logger = logging.getLogger("backend.database")

is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# Pin the driver explicitly rather than relying on SQLAlchemy's default DBAPI
# resolution for a bare "postgresql://" URL, which is not guaranteed to stay
# psycopg2 across SQLAlchemy versions — only psycopg2-binary is a declared
# dependency (see requirements.txt), not psycopg (v3).
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
elif database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)

connect_args = {}
engine_kwargs = {}

if is_sqlite:
    connect_args["check_same_thread"] = False
    engine_kwargs["connect_args"] = connect_args
    if ":memory:" in settings.DATABASE_URL:
        engine_kwargs["poolclass"] = StaticPool
else:
    # Production-grade PostgreSQL pool settings optimized for cloud database poolers
    connect_args["connect_timeout"] = 15
    connect_args["keepalives"] = 1
    connect_args["keepalives_idle"] = 30
    connect_args["keepalives_interval"] = 10
    connect_args["keepalives_count"] = 5
    engine_kwargs["connect_args"] = connect_args
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 5
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(
    database_url,
    **engine_kwargs
)

if not is_sqlite:
    # DateTime columns are naive "timestamp without time zone" but the app writes
    # aware UTC datetimes; PostgreSQL converts those using the session TimeZone.
    # A server configured for Asia/Kolkata (common on State Data Centre hosts)
    # would store IST wall-clock time that the app then reads back as UTC, which
    # makes every token look older than password_changed_at (401 on every call).
    # Pinning each session to UTC keeps stored values in UTC on any server.
    @event.listens_for(engine, "connect")
    def _set_session_timezone_utc(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SET TIME ZONE 'UTC'")
        finally:
            cursor.close()
        dbapi_connection.commit()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_database_connection() -> Tuple[bool, Optional[str]]:
    """
    Verifies database connectivity without exposing connection strings, 
    credentials, or internal stack traces.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return True, None
    except Exception as e:
        # Log generic error locally without leaking sensitive details to caller
        logger.error(f"Database readiness check failed: {type(e).__name__}")
        return False, "Database connection unavailable"

