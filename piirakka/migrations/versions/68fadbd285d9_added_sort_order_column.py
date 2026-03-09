"""added sort_order column

Revision ID: 68fadbd285d9
Revises: 30f04c4e93c9
Create Date: 2026-03-09 14:19:11.298553

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68fadbd285d9'
down_revision: Union[str, None] = '30f04c4e93c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('stations', sa.Column('sort_order', sa.Integer(), nullable=False, server_default="0"))
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_column('stations', 'sort_order')
    # ### end Alembic commands ###
