"""add hostname column to stations

Revision ID: 7068f8bfe270
Revises:
Create Date: 2021-02-06 18:18:57.534985

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7068f8bfe270"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("stations") as batch_op:
        batch_op.add_column(sa.Column("hostname", sa.String))
        batch_op.create_unique_constraint("station_unique_hostname", ["hostname"])


def downgrade():
    with op.batch_alter_table("stations") as batch_op:
        batch_op.drop_column("hostname")
        batch_op.drop_constraint("station_unique_hostname")
