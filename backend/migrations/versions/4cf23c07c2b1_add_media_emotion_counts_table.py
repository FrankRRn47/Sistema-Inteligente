"""add media emotion counts table

Revision ID: 4cf23c07c2b1
Revises: 8e84d888fff6
Create Date: 2025-12-21 12:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '4cf23c07c2b1'
down_revision = '8e84d888fff6'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP TABLE IF EXISTS media_emotion_counts")
    op.create_table(
        'media_emotion_counts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('emotion_label', sa.String(length=20), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['analysis_id'],
            ['media_analyses.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('analysis_id', 'emotion_label', name='uq_media_emotion_counts_analysis_label'),
    )
    op.create_index(
        'ix_media_emotion_counts_analysis_id',
        'media_emotion_counts',
        ['analysis_id'],
    )

    media_table = sa.table(
        'media_analyses',
        sa.column('id', sa.Integer()),
        sa.column('detections', sa.JSON()),
    )
    connection = op.get_bind()
    results = connection.execute(sa.select(media_table.c.id, media_table.c.detections)).fetchall()
    inserts = []
    for analysis_id, detections in results:
        counts = ((detections or {}).get('counts')) or {}
        for label, qty in counts.items():
            normalized_label = (label or '').strip()
            if not normalized_label:
                continue
            try:
                qty_value = int(qty)
            except (TypeError, ValueError):
                continue
            inserts.append(
                {
                    'analysis_id': analysis_id,
                    'emotion_label': normalized_label,
                    'count': max(qty_value, 0),
                    'created_at': datetime.utcnow(),
                }
            )
    if inserts:
        connection.execute(sa.text(
            """
            INSERT INTO media_emotion_counts (analysis_id, emotion_label, count, created_at)
            VALUES (:analysis_id, :emotion_label, :count, :created_at)
            """
        ), inserts)


def downgrade():
    op.drop_index('ix_media_emotion_counts_analysis_id', table_name='media_emotion_counts')
    op.drop_table('media_emotion_counts')
