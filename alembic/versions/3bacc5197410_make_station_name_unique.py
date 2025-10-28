"""Make station name unique

Revision ID: 3bacc5197410
Revises: 3f1f40d79458
Create Date: 2025-10-28 02:41:50.357547

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3bacc5197410'
down_revision: Union[str, None] = '3f1f40d79458'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    with op.batch_alter_table('stations', recreate='always') as batch_op:
        batch_op.alter_column('name', existing_type=sa.String(), nullable=False)
        batch_op.create_unique_constraint('uq_station_name', ['name'])

def downgrade():
    with op.batch_alter_table('stations', recreate='always') as batch_op:
        batch_op.drop_constraint('uq_station_name', type_='unique')
