"""Harden migration metadata exposure.

Revision ID: 20260808_0003
Revises: 20260808_0002
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260808_0003"
down_revision: str | None = "20260808_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Alembic requires its privileged owner to update this table. RLS protects
    # the table from the exposed Supabase API roles while retaining that path.
    op.execute("revoke all on table public.alembic_version from public, anon, authenticated")
    op.execute("alter table public.alembic_version enable row level security")


def downgrade() -> None:
    op.execute("alter table public.alembic_version disable row level security")
