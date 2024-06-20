"""Added role column to User model

Revision ID: 6fce7d4d3424
Revises: 907c26b317aa
Create Date: 2024-06-20 12:20:10.182250

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import MetaData, Table

# revision identifiers, used by Alembic.
revision = '6fce7d4d3424'
down_revision = '907c26b317aa'
branch_labels = None
depends_on = None


def upgrade():
    # Get current table metadata
    conn = op.get_bind()
    metadata = MetaData(bind=conn)
    user_table = Table('user', metadata, autoload_with=conn)

    if 'role' not in [c.name for c in user_table.columns]:
        # Add the column only if it does not exist
        with op.batch_alter_table('user', schema=None) as batch_op:
            batch_op.add_column(sa.Column('role', sa.String(length=10), nullable=False, server_default='user'))
        
        # Remove the default value (SQLite workaround)
        op.execute(
            user_table.update().values(role=None)
        )
        with op.batch_alter_table('user', schema=None) as batch_op:
            batch_op.alter_column('role', server_default=None)


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('role')
