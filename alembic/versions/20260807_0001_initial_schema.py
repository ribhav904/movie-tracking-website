"""Create the initial application schema.

Revision ID: 20260807_0001
Revises:
"""

from collections.abc import Sequence

from alembic import op
from app.db import models  # noqa: F401
from app.db.base import Base

revision: str = "20260807_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


USER_TABLES = [
    "profiles",
    "memberships",
    "library_entries",
    "consumption_cycles",
    "activity_events",
    "custom_lists",
    "custom_list_items",
    "tags",
    "library_entry_tags",
    "arena_ratings",
    "arena_comparisons",
]


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("create schema if not exists app")
    op.execute(
        """
        do $$ begin
          if not exists (select 1 from pg_roles where rolname = 'fastapi_app') then
            create role fastapi_app login noinherit nosuperuser nocreatedb nocreaterole
              noreplication nobypassrls;
          end if;
        end $$;
        """
    )
    Base.metadata.create_all(bind=bind, checkfirst=False)
    op.create_foreign_key(
        "fk_profiles_user_id_auth_users",
        "profiles",
        "users",
        ["user_id"],
        ["id"],
        source_schema="app",
        referent_schema="auth",
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_memberships_user_id_auth_users",
        "memberships",
        "users",
        ["user_id"],
        ["id"],
        source_schema="app",
        referent_schema="auth",
        ondelete="CASCADE",
    )

    # The frontend uses Supabase Auth only. Application tables are not Data API resources.
    op.execute("revoke all on schema app from public, anon, authenticated")
    op.execute("grant usage on schema app to fastapi_app")
    op.execute("grant select, insert, update, delete on all tables in schema app to fastapi_app")
    op.execute("grant usage, select on all sequences in schema app to fastapi_app")
    op.execute("revoke update, delete on app.arena_comparisons from fastapi_app")
    op.execute(
        """
        alter default privileges for role postgres in schema public
          revoke select, insert, update, delete on tables from anon, authenticated;
        alter default privileges for role postgres in schema public
          revoke execute on functions from anon, authenticated;
        alter default privileges for role postgres in schema public
          revoke usage, select on sequences from anon, authenticated;
        alter default privileges for role postgres in schema public
          revoke execute on functions from public;
        """
    )

    for table in USER_TABLES:
        op.execute(f"alter table app.{table} enable row level security")
        op.execute(f"alter table app.{table} force row level security")

    own_only = [
        "library_entries",
        "consumption_cycles",
        "activity_events",
        "custom_lists",
        "custom_list_items",
        "tags",
        "library_entry_tags",
        "arena_ratings",
        "arena_comparisons",
    ]
    for table in own_only:
        op.execute(
            f"""
            create policy {table}_isolate_user on app.{table}
            for all to fastapi_app
            using (user_id = nullif(current_setting('app.current_user_id', true), '')::uuid)
            with check (user_id = nullif(current_setting('app.current_user_id', true), '')::uuid)
            """
        )

    for table in ["profiles", "memberships"]:
        op.execute(
            f"""
            create policy {table}_self_or_owner on app.{table}
            for all to fastapi_app
            using (
              user_id = nullif(current_setting('app.current_user_id', true), '')::uuid
              or current_setting('app.current_user_role', true) = 'owner'
            )
            with check (
              user_id = nullif(current_setting('app.current_user_id', true), '')::uuid
              or current_setting('app.current_user_role', true) = 'owner'
            )
            """
        )
    op.execute(
        """
        alter table app.admin_audit_log enable row level security;
        alter table app.admin_audit_log force row level security;
        create policy admin_audit_owner_only on app.admin_audit_log
        for all to fastapi_app
        using (current_setting('app.current_user_role', true) = 'owner')
        with check (current_setting('app.current_user_role', true) = 'owner');
        """
    )


def downgrade() -> None:
    op.execute("drop schema if exists app cascade")
