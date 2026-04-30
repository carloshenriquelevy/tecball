"""create all tables

Revision ID: 0001
Revises:
Create Date: 2026-04-29 08:48:42.387392

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

stage_enum = sa.Enum('GROUP', 'R32', 'R16', 'QF', 'SF', 'THIRD', 'FINAL', name='stage')


def upgrade() -> None:
    stage_enum.create(op.get_bind(), checkfirst=True)

    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=150), nullable=False),
        sa.Column('password_hash', sa.String(length=200), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_id', 'users', ['id'])

    op.create_table('teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('flag', sa.String(length=10), nullable=False),
        sa.Column('confederation', sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_teams_id', 'teams', ['id'])

    op.create_table('groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=5), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_groups_id', 'groups', ['id'])

    op.create_table('group_teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'team_id', name='uq_group_team'),
    )
    op.create_index('ix_group_teams_id', 'group_teams', ['id'])

    op.create_table('matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_number', sa.Integer(), nullable=False),
        sa.Column('stage', stage_enum, nullable=False),
        sa.Column('home_team_id', sa.Integer(), nullable=True),
        sa.Column('away_team_id', sa.Integer(), nullable=True),
        sa.Column('home_score', sa.Integer(), nullable=True),
        sa.Column('away_score', sa.Integer(), nullable=True),
        sa.Column('match_date', sa.DateTime(), nullable=True),
        sa.Column('group_id', sa.Integer(), nullable=True),
        sa.Column('is_finished', sa.Boolean(), nullable=True),
        sa.Column('label', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['away_team_id'], ['teams.id']),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.ForeignKeyConstraint(['home_team_id'], ['teams.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('match_number'),
    )
    op.create_index('ix_matches_id', 'matches', ['id'])

    op.create_table('bets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('home_score', sa.Integer(), nullable=False),
        sa.Column('away_score', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'match_id', name='uq_bet_user_match'),
    )
    op.create_index('ix_bets_id', 'bets', ['id'])

    op.create_table('special_bets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('champion_id', sa.Integer(), nullable=True),
        sa.Column('runner_up_id', sa.Integer(), nullable=True),
        sa.Column('third_id', sa.Integer(), nullable=True),
        sa.Column('fourth_id', sa.Integer(), nullable=True),
        sa.Column('points', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['champion_id'], ['teams.id']),
        sa.ForeignKeyConstraint(['fourth_id'], ['teams.id']),
        sa.ForeignKeyConstraint(['runner_up_id'], ['teams.id']),
        sa.ForeignKeyConstraint(['third_id'], ['teams.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_special_bets_id', 'special_bets', ['id'])


def downgrade() -> None:
    op.drop_table('special_bets')
    op.drop_table('bets')
    op.drop_table('matches')
    op.drop_table('group_teams')
    op.drop_table('groups')
    op.drop_table('teams')
    op.drop_table('users')
    stage_enum.drop(op.get_bind(), checkfirst=True)
