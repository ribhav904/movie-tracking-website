# Entertainment Tracker API

FastAPI backend for a private movie, TV, game, and book tracker. FastAPI is the only application
data API. Supabase provides hosted PostgreSQL and email/password authentication.

## Current architecture

- FastAPI runs on your local machine.
- Application data is stored in a remote Supabase PostgreSQL project.
- The frontend uses Supabase directly only for authentication.
- The frontend sends the Supabase access token to FastAPI as a Bearer token.
- Supabase Data API, Edge Functions, Realtime, Storage, and Cron are not used.
- Movies and TV use TMDB, games use IGDB, and books use Google Books with Open Library fallback.

## Prerequisites

- Git
- `uv` 0.8.8 or later
- A free Supabase project in the Mumbai region
- Free developer credentials for the media providers you want to enable

Install `uv` on Windows:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.8.8/install.ps1 | iex"
```

## Supabase project setup

1. Create a Supabase project in Mumbai.
2. In **Authentication > Providers**, keep email/password enabled.
3. Disable public user signup.
4. In **Authentication > Signing Keys**, migrate to and activate an asymmetric signing key.
5. In **Integrations > Data API**, disable the Data API.
6. Copy the session-pooler connection string on port 5432.
7. Copy `.env.example` to `.env` and fill in the migration connection URL.

The first Alembic migration creates the `app` schema and a login role named `fastapi_app`. After
running it, set a strong runtime password from the Supabase SQL editor. Do not put this password in
Git:

```sql
alter role fastapi_app with password 'GENERATE_A_LONG_RANDOM_PASSWORD';
```

Use the session-pooler username format shown by Supabase for the custom role, normally
`fastapi_app.<project-ref>`, to build `DATABASE_URL`.

## Local setup

```powershell
uv sync --all-groups
Copy-Item .env.example .env
# Edit .env before continuing.
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

- API documentation: <http://127.0.0.1:8000/docs>
- OpenAPI document: <http://127.0.0.1:8000/openapi.json>
- Liveness: <http://127.0.0.1:8000/health/live>
- Database readiness: <http://127.0.0.1:8000/health/ready>

## Frontend

The frontend lives in `frontend/`. It is a TypeScript React application with a deliberate
light/dark design system, Supabase Auth, and a FastAPI-only application-data client.

```powershell
cd frontend
Copy-Item .env.example .env.local
# Add the local FastAPI URL and Supabase publishable credentials.
npm.cmd install
npm.cmd run dev
```

The local UI is available at <http://localhost:3000>. When `.env.local` is not configured, the
interface enters a clearly marked, non-persistent preview mode so the design can be inspected
without pretending to use real data. When configuration is present, Supabase is used only for
email/password authentication and all media, library, tracking, reporting, Arena, and
recommendation data goes through FastAPI.

Frontend quality checks:

```powershell
cd frontend
npm.cmd run lint
npm.cmd test
```

The design, UX, technical architecture, and delivery plan are documented in
[`docs/FRONTEND_PLAN.md`](docs/FRONTEND_PLAN.md).

## Bootstrap the owner

Create the first user from **Authentication > Users** in the Supabase dashboard. Confirm the email,
then copy the user's UUID and run:

```sql
insert into app.profiles (user_id, display_name, timezone, preferences)
values ('USER_UUID', 'Your Name', 'Asia/Kolkata', '{}'::jsonb);

insert into app.memberships (user_id, role, active)
values ('USER_UUID', 'owner', true);
```

After the owner signs in, create the other two accounts through `POST /api/v1/admin/users`.

## Frontend authentication contract

The frontend calls Supabase Auth with the publishable key:

```typescript
const { data, error } = await supabase.auth.signInWithPassword({ email, password })
```

It then sends the access token to FastAPI:

```http
Authorization: Bearer ACCESS_TOKEN
```

No frontend request should use Supabase REST or GraphQL for application data.

## Provider credentials

- TMDB: set `TMDB_ACCESS_TOKEN` to the read-access Bearer token.
- IGDB: set `IGDB_CLIENT_ID` and `IGDB_CLIENT_SECRET` from a Twitch developer application.
- Google Books: set `GOOGLE_BOOKS_API_KEY` to a restricted API key.
- Open Library: set `OPEN_LIBRARY_CONTACT` to a real contact email for the required User-Agent.

Search responses are not persisted. Details are cached when imported or opened. Provider images
remain externally hosted.

## Database migrations

Create migrations with Alembic and review generated SQL before applying it:

```powershell
uv run alembic revision --autogenerate -m "describe_change"
$env:DATABASE_MIGRATION_URL = "postgresql+psycopg://user:password@host/db"
uv run alembic upgrade head --sql
uv run alembic upgrade head
```

Never edit an applied migration. Add a forward corrective migration instead. The application does
not run migrations at startup.

## Quality checks

```powershell
uv run ruff format --check .
uv run ruff check .
uv run mypy app
uv run pytest --cov=app --cov-report=term-missing
```

Remote integration tests are opt-in and must use dedicated test users:

```powershell
uv run pytest -m integration
```

## GitHub workflow

- `main` is the only long-lived branch.
- Use `feat/<issue>-description`, `fix/<issue>-description`, `chore/<issue>-description`, or
  `docs/<issue>-description`.
- Open a pull request for every change, squash-merge it, and delete the branch.
- Require CI, linear history, and resolved conversations on `main`.
- Do not add remote Supabase or provider secrets to pull-request workflows.

## Future Render deployment

Render is not configured or deployed yet. The app is ready to use this start command later:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Create a separate production Supabase project before deploying. Do not reuse the current remote
development project as production.
