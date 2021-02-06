"""add optional sensor tag

Revision ID: 2aba3fc904e2
Revises: 7068f8bfe270
Create Date: 2021-02-06 18:30:43.027491

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2aba3fc904e2"
down_revision = "7068f8bfe270"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sensors") as batch_op:
        batch_op.add_column(sa.Column("tag", sa.String, nullable=True))
        batch_op.drop_index("ix_sensors_name")
        batch_op.create_unique_constraint("sensor_unique_name", ["name"])
        batch_op.create_unique_constraint("sensor_unique_name_tag", ["name", "tag"])


def downgrade():
    with op.batch_alter_table("sensors") as batch_op:
        batch_op.drop_column("tag")
        batch_op.drop_constraint("sensor_unique_name_tag")
        # batch_op.create_unique_constraint("sensor_unique_name", ["name"])
