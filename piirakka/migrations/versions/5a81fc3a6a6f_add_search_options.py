"""Add search options

Revision ID: 5a81fc3a6a6f
Revises: 68fadbd285d9
Create Date: 2026-08-08 23:47:42.952948

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5a81fc3a6a6f"
down_revision: Union[str, None] = "68fadbd285d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

search_options_table = sa.Table(
    "search_options",
    sa.MetaData(),
    sa.Column("key", sa.String),
    sa.Column("is_enabled", sa.Boolean),
)


def upgrade() -> None:
    op.create_table(
        "search_options",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.PrimaryKeyConstraint("key"),
    )

    op.bulk_insert(
        search_options_table,
        [
            {"key": "spotify_desktop", "is_enabled": True},
            {"key": "spotify_web", "is_enabled": True},
            {"key": "apple_music_desktop", "is_enabled": True},
            {"key": "apple_music_web", "is_enabled": True},
            {"key": "youtube", "is_enabled": True},
            {"key": "bandcamp", "is_enabled": True},
        ],
    )


def downgrade() -> None:
    op.drop_table("search_options")
