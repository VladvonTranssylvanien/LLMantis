"""Initial schema

Revision ID: be2494f1af40
Revises:
Create Date: 2026-08-15 19:41:27.210499

This migration was generated empty. Autogenerate was run against a database
whose tables already existed, so it saw no difference and wrote `pass`, and
nothing else in the repository ever created them — there has never been a
create_all() call (`git log -S "create_all"` is empty).

The consequence only shows on a machine that has never had the tables: every
later migration ALTERs a table that was never created, and `alembic upgrade
head` dies on "relation \"scans\" does not exist". A fresh clone could not
build the database at all.

The tables below are the five the schema started with, in the shape they had
at THIS revision — deliberately without the columns that later migrations add:

    scans.library_version           b5f8b56f3812
    ownership_verifications.token   d560784b731d
    ownership_verifications.expires_at
    targets.retention               a31bbdafd5e3
    scans.status
    results.judge_reason

An existing database is already stamped past this revision, so this never
re-runs there. It only changes what a new database gets.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'be2494f1af40'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain'),
    )
    op.create_table(
        'targets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('canary', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'ownership_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('method', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'scans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('duration_s', sa.Float(), nullable=False),
        sa.Column('grade', sa.String(length=1), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('error_rate', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['target_id'], ['targets.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attack_id', sa.String(length=255), nullable=False),
        sa.Column('verdict', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.String(length=50), nullable=False),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('method', sa.String(length=50), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('results')
    op.drop_table('scans')
    op.drop_table('ownership_verifications')
    op.drop_table('targets')
    op.drop_table('organizations')
