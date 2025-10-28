"""Create stations table

Revision ID: 3f1f40d79458
Revises: 
Create Date: 2024-11-28 20:04:52.375944

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid


# revision identifiers, used by Alembic.
revision: str = '3f1f40d79458'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'stations',
        sa.Column('station_id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('added_on', sa.DateTime(), default=sa.func.current_timestamp()),
    )


def downgrade() -> None:
    op.drop_table('stations')
