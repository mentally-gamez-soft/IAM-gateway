"""Add profile fields to gw_user (US-011).

Revision ID: 839e3f1c24567
Revises: 838d0e2f34567
Create Date: 2026-02-23 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "839e3f1c24567"
down_revision = "838d0e2f34567"
branch_labels = None
depends_on = None


def upgrade():
    """Add user profile columns to gw_user table."""
    with op.batch_alter_table("gw_user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("display_name", sa.String(length=80), nullable=True)
        )
        batch_op.add_column(
            sa.Column("avatar_url", sa.String(length=255), nullable=True)
        )
        batch_op.add_column(sa.Column("bio", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "language_preference",
                sa.String(length=5),
                nullable=False,
                server_default="en",
            )
        )
        batch_op.add_column(
            sa.Column(
                "timezone",
                sa.String(length=50),
                nullable=False,
                server_default="UTC",
            )
        )
        batch_op.add_column(
            sa.Column("profile_updated_at", sa.DateTime(), nullable=True)
        )


def downgrade():
    """Remove user profile columns from gw_user table."""
    with op.batch_alter_table("gw_user", schema=None) as batch_op:
        batch_op.drop_column("profile_updated_at")
        batch_op.drop_column("timezone")
        batch_op.drop_column("language_preference")
        batch_op.drop_column("bio")
        batch_op.drop_column("avatar_url")
        batch_op.drop_column("display_name")
