"""Add GDPR compliance fields: deleted_at, consent columns to gw_user and user_consent table.

Revision ID: 838d0e2f34567
Revises: 837c9d1f23456
Create Date: 2026-02-21 22:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "838d0e2f34567"
down_revision = "837c9d1f23456"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Return True when a column already exists in the target table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in cols


def upgrade():
    """Add GDPR fields to gw_user and create user_consent table."""
    # Add deleted_at column to gw_user (dedicated deletion timestamp for GDPR audit)
    if not _column_exists("gw_user", "deleted_at"):
        op.add_column(
            "gw_user",
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
        )
    # Add user-level consent flag and timestamp
    if not _column_exists("gw_user", "consent_given"):
        op.add_column(
            "gw_user",
            sa.Column("consent_given", sa.Boolean(), nullable=True),
        )
    if not _column_exists("gw_user", "consent_at"):
        op.add_column(
            "gw_user",
            sa.Column("consent_at", sa.DateTime(), nullable=True),
        )

    # Create the user_consent table for per-type consent tracking
    op.create_table(
        "user_consent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("consent_type", sa.String(length=50), nullable=False),
        sa.Column(
            "granted", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("granted_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["gw_user.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="Tracks GDPR consent entries per user per consent type.",
        if_not_exists=True,
    )
    # Create indexes only if they don't already exist
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_indexes = {
        idx["name"] for idx in inspector.get_indexes("user_consent")
    }
    if "ix_user_consent_user_id" not in existing_indexes:
        op.create_index(
            op.f("ix_user_consent_user_id"),
            "user_consent",
            ["user_id"],
            unique=False,
        )
    if "ix_user_consent_consent_type" not in existing_indexes:
        op.create_index(
            op.f("ix_user_consent_consent_type"),
            "user_consent",
            ["consent_type"],
            unique=False,
        )


def downgrade():
    """Remove GDPR fields and user_consent table."""
    op.drop_index(
        op.f("ix_user_consent_consent_type"), table_name="user_consent"
    )
    op.drop_index(op.f("ix_user_consent_user_id"), table_name="user_consent")
    op.drop_table("user_consent")
    op.drop_column("gw_user", "consent_at")
    op.drop_column("gw_user", "consent_given")
    op.drop_column("gw_user", "deleted_at")
