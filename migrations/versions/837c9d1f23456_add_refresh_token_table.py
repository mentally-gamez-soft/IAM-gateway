"""Add RefreshToken model for JWT refresh token mechanism.

Revision ID: 837c9d1f23456
Revises: 836b8c9f12345
Create Date: 2026-02-18 18:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "837c9d1f23456"
down_revision = "836b8c9f12345"
branch_labels = None
depends_on = None


def upgrade():
    """Create refresh_token table."""
    op.create_table(
        "refresh_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(255), nullable=False, unique=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_on", sa.DateTime(), nullable=False),
        sa.Column("expires_on", sa.DateTime(), nullable=False),
        sa.Column(
            "revoked", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("revoked_on", sa.DateTime(), nullable=True),
        sa.Column("replaced_by", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["gw_user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="Stores refresh tokens with family-based reuse detection.",
    )
    # Create indices for faster lookups
    op.create_index(
        op.f("ix_refresh_token_user_id"),
        "refresh_token",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_refresh_token_family_id"),
        "refresh_token",
        ["family_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_refresh_token_token"),
        "refresh_token",
        ["token"],
        unique=False,
    )


def downgrade():
    """Drop refresh_token table."""
    op.drop_index(op.f("ix_refresh_token_token"), table_name="refresh_token")
    op.drop_index(
        op.f("ix_refresh_token_family_id"), table_name="refresh_token"
    )
    op.drop_index(op.f("ix_refresh_token_user_id"), table_name="refresh_token")
    op.drop_table("refresh_token")
