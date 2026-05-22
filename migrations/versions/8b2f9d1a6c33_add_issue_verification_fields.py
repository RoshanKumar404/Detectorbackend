"""Add issue verification fields

Revision ID: 8b2f9d1a6c33
Revises: 0ea785ace380
Create Date: 2026-05-22 11:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '8b2f9d1a6c33'
down_revision = '0ea785ace380'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('issues', schema=None) as batch_op:
        batch_op.add_column(sa.Column('verification_status', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('verification_weight', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('fraud_flags', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('device_fingerprint', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('location_source', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('exif_captured_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('exif_latitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('exif_longitude', sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('issues', schema=None) as batch_op:
        batch_op.drop_column('exif_longitude')
        batch_op.drop_column('exif_latitude')
        batch_op.drop_column('exif_captured_at')
        batch_op.drop_column('location_source')
        batch_op.drop_column('device_fingerprint')
        batch_op.drop_column('fraud_flags')
        batch_op.drop_column('verification_weight')
        batch_op.drop_column('verification_status')
