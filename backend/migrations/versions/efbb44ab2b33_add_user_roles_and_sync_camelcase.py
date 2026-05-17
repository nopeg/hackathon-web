from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'efbb44ab2b33'
down_revision = '7ef0358394a9'
branch_labels = None
depends_on = None

def upgrade() -> None:
    user_role_enum = sa.Enum('USER', 'MODERATOR', 'ADMIN', name='userrole')
    user_role_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('users', sa.Column('role', sa.Enum('USER', 'MODERATOR', 'ADMIN', name='userrole'), nullable=False, server_default='USER'))
    op.drop_column('users', 'isVerified')
    op.drop_column('users', 'createdAt')

def downgrade() -> None:
    op.add_column('users', sa.Column('createdAt', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('isVerified', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('users', 'role')

    user_role_enum = sa.Enum('USER', 'MODERATOR', 'ADMIN', name='userrole')
    user_role_enum.drop(op.get_bind(), checkfirst=True)