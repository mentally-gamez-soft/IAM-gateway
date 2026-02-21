"""Add password reset token field to GwUser model.

Revision ID: 836b8c9f12345
Revises: 835da9b57698
Create Date: 2026-02-18 17:15:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "836b8c9f12345"
down_revision = "835da9b57698"
branch_labels = None
depends_on = None


def upgrade():
    """Add last_password_reset_token column to gw_user table."""
    op.add_column(
        "gw_user",
        sa.Column("last_password_reset_token", sa.String(100), nullable=True),
    )


def downgrade():
    """Remove last_password_reset_token column from gw_user table."""
    op.drop_column("gw_user", "last_password_reset_token")
