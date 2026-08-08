"""Replace session activity with completion records.

Revision ID: 20260808_0002
Revises: 20260807_0001
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260808_0002"
down_revision: str | None = "20260807_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # This project has no retained user data yet. The previous session/activity
    # model is intentionally discarded rather than converted into misleading
    # completion history.
    op.execute("delete from app.activity_events")
    op.execute("delete from app.consumption_cycles")
    op.execute("delete from app.library_entries")
    op.execute("drop table if exists app.activity_events")
    op.execute("drop table if exists app.consumption_cycles")
    op.execute("drop type if exists app.activity_kind")
    op.execute("drop type if exists app.cycle_state")
    op.execute("alter type app.library_status add value if not exists 'caught_up'")

    # The first migration builds ORM metadata wholesale. IF NOT EXISTS keeps a
    # new database install compatible with that historical migration while
    # making this revision authoritative for permissions and RLS.
    op.execute(
        """
        create table if not exists app.consumption_records (
          id uuid primary key,
          user_id uuid not null references app.profiles(user_id) on delete cascade,
          library_entry_id uuid not null references app.library_entries(id) on delete cascade,
          sequence_number integer not null,
          completed_on date null,
          season_id uuid null references app.tv_seasons(id) on delete cascade,
          rating numeric(3, 1) null,
          notes text null,
          created_at timestamptz not null default now(),
          updated_at timestamptz not null default now(),
          unique (library_entry_id, sequence_number),
          constraint consumption_rating_half_steps check (
            rating is null or (rating >= 1 and rating <= 10 and rating * 2 = trunc(rating * 2))
          )
        )
        """
    )
    op.execute(
        "create index if not exists ix_consumption_records_user_id "
        "on app.consumption_records (user_id)"
    )
    op.execute(
        "create index if not exists ix_consumption_records_library_entry_id "
        "on app.consumption_records (library_entry_id)"
    )
    op.execute(
        "create index if not exists ix_consumption_records_season_id "
        "on app.consumption_records (season_id)"
    )
    op.execute(
        "create index if not exists ix_consumption_records_user_completed_on "
        "on app.consumption_records (user_id, completed_on desc) where completed_on is not null"
    )
    op.execute("grant select, insert, update, delete on app.consumption_records to fastapi_app")
    op.execute("alter table app.consumption_records enable row level security")
    op.execute("alter table app.consumption_records force row level security")
    op.execute("drop policy if exists consumption_records_isolate_user on app.consumption_records")
    op.execute(
        """
        create policy consumption_records_isolate_user on app.consumption_records
        for all to fastapi_app
        using (user_id = nullif(current_setting('app.current_user_id', true), '')::uuid)
        with check (user_id = nullif(current_setting('app.current_user_id', true), '')::uuid)
        """
    )


def downgrade() -> None:
    # Enum values cannot be safely removed on a shared PostgreSQL type. Use a
    # forward corrective migration instead of downgrading real tracker data.
    op.execute("drop table if exists app.consumption_records")
