"""add media analyses table

Revision ID: 8e84d888fff6
Revises: e1bdef4965dc
Create Date: 2025-12-20 20:35:11.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '8e84d888fff6'
down_revision = 'e1bdef4965dc'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table('media_analyses'):
        return

    op.create_table(
        'media_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('media_type', sa.String(length=20), nullable=False),
        sa.Column('source_type', sa.String(length=20), nullable=False),
        sa.Column('channel', sa.String(length=40), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=True),
        sa.Column('original_path', sa.String(length=255), nullable=False),
        sa.Column('snapshot_path', sa.String(length=255), nullable=False),
        sa.Column('dominant_emotion', sa.String(length=20), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('detections', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('media_analyses')
